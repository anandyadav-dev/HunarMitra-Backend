from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.crud_user import user as user_crud
from app.models.worker import Worker
from app.models.contractor import Contractor
from app.schemas.user import UserCreate, UserResponse, OTPRequest, OTPVerify
from app.schemas.token import Token
from app.services import otp as otp_service
from app.core import security

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(obj_in: UserCreate, db: Session = Depends(deps.get_db)):
    """
    Registers a new user (customer, worker, or contractor) with their phone number.
    If the user registers as a worker, a worker profile record is initialized.
    """
    existing_user = user_crud.get_by_phone_number(db, phone_number=obj_in.phone_number)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this phone number is already registered."
        )
    
    # Create the user and initialize wallet
    new_user = user_crud.create(db, obj_in=obj_in)
    
    # If the role is worker (or sub-role), also create an uncategorized worker profile record
    is_worker = False
    for role in new_user.roles:
        curr = role
        while curr:
            if curr.name.lower() == "worker":
                is_worker = True
                break
            curr = curr.parent
        if is_worker:
            break
            
    if is_worker:
        worker_profile = Worker(
            user_id=new_user.id,
            category="Uncategorized",
            pricing_per_hour=Decimal("0.00"),
            experience_years=0,
            availability_status="unavailable"
        )
        db.add(worker_profile)
        db.commit()
        db.refresh(new_user)
        
    is_contractor = False
    for role in new_user.roles:
        curr = role
        while curr:
            if curr.name.lower() == "contractor":
                is_contractor = True
                break
            curr = curr.parent
        if is_contractor:
            break
            
    if is_contractor:
        contractor_profile = Contractor(
            user_id=new_user.id,
            company_name="Pending Details",
            experience_years=0
        )
        db.add(contractor_profile)
        db.commit()
        db.refresh(new_user)
        
    return new_user

@router.post("/login-otp", status_code=status.HTTP_200_OK)
def login_otp(obj_in: OTPRequest, db: Session = Depends(deps.get_db)):
    """
    Initiates the phone OTP login process. Sends a verification OTP (mocked) to the device.
    """
    user_obj = user_crud.get_by_phone_number(db, phone_number=obj_in.phone_number)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not registered. Please register first."
        )
    
    # Mock send OTP
    otp_service.generate_and_send_otp(phone_number=obj_in.phone_number)
    return {"message": "OTP verification code successfully sent (mocked)."}

@router.post("/verify-otp", response_model=Token)
def verify_otp(obj_in: OTPVerify, db: Session = Depends(deps.get_db)):
    """
    Verifies the OTP code received by the client and issues a JWT token.
    Marks user status as verified if verified for the first time.
    """
    is_valid = otp_service.verify_otp(phone_number=obj_in.phone_number, otp=obj_in.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code."
        )
        
    user_obj = user_crud.get_by_phone_number(db, phone_number=obj_in.phone_number)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with phone number not found."
        )
        
    # Set verification flag true on successful verification
    if not user_obj.is_verified:
        user_obj.is_verified = True
        db.add(user_obj)
        db.commit()
        db.refresh(user_obj)
        
    access_token = security.create_access_token(subject=user_obj.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


from pydantic import BaseModel

class AdminPasswordLogin(BaseModel):
    phone_number: str
    password: str

@router.post("/admin-login", response_model=Token)
def admin_login(obj_in: AdminPasswordLogin, db: Session = Depends(deps.get_db)):
    """
    Authenticate an administrator via phone number and password.
    Only allows access if the user is an admin.
    """
    user_obj = user_crud.get_by_phone_number(db, phone_number=obj_in.phone_number)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not registered."
        )
        
    # Verify the user has the admin role
    if not deps.check_role_recursive(user_obj.roles, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. Only administrator accounts can log in here."
        )
        
    # Verify the password
    if not user_obj.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is not set for this account. Please log in using OTP."
        )
        
    if not security.verify_password(obj_in.password, user_obj.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password."
        )
        
    access_token = security.create_access_token(subject=user_obj.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/swagger-login", response_model=Token, include_in_schema=False)
def swagger_login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Dedicated endpoint for Swagger UI authentication.
    Takes Form Data (username, password) instead of JSON.
    username = phone_number
    password = OTP (or Admin Password)
    """
    user_obj = user_crud.get_by_phone_number(db, phone_number=form_data.username)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
        
    # Verify OTP for everyone (Admins and normal users)
    is_valid = otp_service.verify_otp(phone_number=form_data.username, otp=form_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code."
        )
            
    access_token = security.create_access_token(subject=user_obj.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

