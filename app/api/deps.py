from typing import Generator
import jwt
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.crud.crud_user import user as user_crud
from app.models.user import User

# OAuth2PasswordBearer automatically parses standard Bearer Authorization headers
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/swagger-login", 
    auto_error=False
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to yield database session and clean it up on request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Decodes the Bearer token, validates signatures, and returns the User object.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user_id = UUID(str(user_id_str))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        
    user_obj = user_crud.get(db, id=user_id)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    return user_obj

def check_role_recursive(user_roles: list, allowed_names: list[str]) -> bool:
    """
    Recursively check if user holds any of the allowed role names or inherits
    them through a parent role.
    """
    allowed_names_lower = [name.lower() for name in allowed_names]
    active_roles = set()
    for role in user_roles:
        curr = role
        while curr:
            active_roles.add(curr.name.lower())
            curr = curr.parent  # Move up hierarchy
    return any(name in active_roles for name in allowed_names_lower)

class RoleChecker:
    """
    Endpoint dependency enforcing dynamic and hierarchical RBAC permissions.
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not check_role_recursive(current_user.roles, self.allowed_roles):
            # Print current roles list for logging/debugging
            user_roles_str = ", ".join([r.name for r in current_user.roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action forbidden. User roles: '{user_roles_str}'. Requires one of: {self.allowed_roles}",
            )
        return current_user

# Predefined role checking dependencies
require_customer = RoleChecker(["customer"])
require_worker = RoleChecker(["worker"])
require_contractor = RoleChecker(["contractor"])
require_worker_or_contractor = RoleChecker(["worker", "contractor"])
