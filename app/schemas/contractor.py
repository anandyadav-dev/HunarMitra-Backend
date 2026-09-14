from pydantic import UUID4, BaseModel, Field
from typing import Optional
from app.models.worker import KycStatus
from app.schemas.user import UserResponse

class ContractorBase(BaseModel):
    company_name: Optional[str] = Field(None, max_length=100)
    gst_number: Optional[str] = Field(None, max_length=15)
    pan_number: Optional[str] = Field(None, max_length=10)
    business_license: Optional[str] = None
    profile_picture: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    work_types: Optional[list[str]] = None
    experience_years: Optional[int] = Field(0, ge=0)

class ContractorCreate(ContractorBase):
    pass

class ContractorUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=100)
    gst_number: Optional[str] = Field(None, max_length=15)
    pan_number: Optional[str] = Field(None, max_length=10)
    business_license: Optional[str] = None
    profile_picture: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    work_types: Optional[list[str]] = None
    experience_years: Optional[int] = Field(None, ge=0)

class ContractorResponse(ContractorBase):
    id: UUID4
    user_id: UUID4
    kyc_status: KycStatus
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True

class ContractorDetailedResponse(ContractorResponse):
    user: UserResponse

    class Config:
        from_attributes = True
