from datetime import datetime
from pydantic import UUID4, BaseModel, Field
from typing import Optional, List
from decimal import Decimal

class RoleResponse(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    phone_number: str = Field(..., max_length=15, pattern=r"^\+?[1-9]\d{1,14}$")
    full_name: Optional[str] = Field(None, max_length=100)
    language_preference: str = "English"
    city: Optional[str] = Field(None, max_length=100)
    location_lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    location_lng: Optional[Decimal] = Field(None, ge=-180, le=180)

class UserCreate(UserBase):
    role: str = Field(..., description="The role name to register as (e.g. 'customer', 'worker', 'contractor')")

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
    phone_number: str = Field(..., max_length=15, pattern=r"^\+?[1-9]\d{1,14}$")

class OTPVerify(BaseModel):
    phone_number: str = Field(..., max_length=15, pattern=r"^\+?[1-9]\d{1,14}$")
    otp: str = Field(..., min_length=6, max_length=6)
