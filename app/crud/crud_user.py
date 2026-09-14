from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.user import User
from app.models.role import Role
from app.models.wallet import Wallet
from app.models.contractor import Contractor
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_phone_number(self, db: Session, *, phone_number: str) -> Optional[User]:
        """
        Retrieves a user by their phone number.
        """
        return db.query(User).filter(User.phone_number == phone_number).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Creates a new user, resolves roles/sub-roles, and automatically initializes 
        wallets, worker profiles, or contractor profiles.
        """
        obj_in_data = obj_in.model_dump()
        requested_role_name = obj_in_data.pop("role", "customer").strip()
        
        # 1. Create core user model instance
        db_obj = User(**obj_in_data)
        
        # 2. Query and link the database Role
        db_role = db.query(Role).filter(
            func.lower(Role.name) == requested_role_name.lower()
        ).first()
        
        # Fallback to standard 'customer' role if mapping fails
        if not db_role:
            db_role = db.query(Role).filter(Role.name == "customer").first()
            
        if db_role:
            db_obj.roles.append(db_role)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # 3. Handle specific profile creations depending on roles
        if db_role:
            # Traversal helper to check root roles
            active_role_names = set()
            curr = db_role
            while curr:
                active_role_names.add(curr.name.lower())
                curr = curr.parent
                
            # If contractor (or sub-contractor), initialize contractor profile
            if "contractor" in active_role_names:
                contractor_profile = Contractor(
                    user_id=db_obj.id,
                    company_name=None
                )
                db.add(contractor_profile)
                
        # 4. Initialize user's wallet
        wallet = Wallet(user_id=db_obj.id, balance=0.0)
        db.add(wallet)
        
        db.commit()
        db.refresh(db_obj)
        
        return db_obj

user = CRUDUser(User)
