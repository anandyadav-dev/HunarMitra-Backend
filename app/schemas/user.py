from datetime import datetime
from pydantic import UUID4, BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal

class RoleResponse(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    phone_number: str = Field(..., max_length=15)
    full_name: Optional[str] = Field(None, max_length=100)
    language_preference: str = "English"
    city: Optional[str] = Field(None, max_length=100)
    location_lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    location_lng: Optional[Decimal] = Field(None, ge=-180, le=180)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        import re
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format. Must include country code (e.g., +919999999900).")
        return v

class UserCreate(UserBase):
    role: str = Field(..., description="The role name to register as (e.g. 'customer', 'worker', 'contractor')")
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["customer", "worker", "contractor"]
        if v.lower() not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return v.lower()

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    language_preference: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    location_lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    location_lng: Optional[Decimal] = Field(None, ge=-180, le=180)

class UserResponse(UserBase):
    id: UUID4
    is_verified: bool
    created_at: datetime
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True

class OTPRequest(BaseModel):
    phone_number: str = Field(..., max_length=15)
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        import re
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format. Must include country code (e.g., +919999999900).")
        return v

class OTPVerify(BaseModel):
    phone_number: str = Field(..., max_length=15)
    otp: str = Field(..., min_length=4, max_length=6)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        import re
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format. Must include country code (e.g., +919999999900).")
        return v
        
    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP must contain only digits.")
        return v
