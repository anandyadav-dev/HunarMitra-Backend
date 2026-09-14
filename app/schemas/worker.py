from decimal import Decimal
from pydantic import UUID4, BaseModel, Field
from typing import Optional
from app.schemas.user import UserResponse
from app.models.worker import KycStatus, AvailabilityStatus

class WorkerBase(BaseModel):
    category: str = Field(..., max_length=50, examples=["Plumber", "Electrician"])
    experience_years: int = Field(0, ge=0)
    pricing_per_hour: Decimal = Field(..., gt=0)
    bio: Optional[str] = None
    availability_status: AvailabilityStatus = AvailabilityStatus.available_now
    location_lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    location_lng: Optional[Decimal] = Field(None, ge=-180, le=180)
    profile_picture: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    area_mohalla: Optional[str] = Field(None, max_length=100)
    working_radius_km: Optional[int] = Field(10, ge=1)
    additional_skills: Optional[list[str]] = None
    languages: Optional[list[str]] = None

class WorkerCreate(WorkerBase):
    pass

class WorkerUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=50)
    experience_years: Optional[int] = Field(None, ge=0)
    pricing_per_hour: Optional[Decimal] = Field(None, gt=0)
    bio: Optional[str] = None
    availability_status: Optional[AvailabilityStatus] = None
    location_lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    location_lng: Optional[Decimal] = Field(None, ge=-180, le=180)
    profile_picture: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    area_mohalla: Optional[str] = Field(None, max_length=100)
    working_radius_km: Optional[int] = Field(None, ge=1)
    additional_skills: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    aadhaar_image_front: Optional[str] = None
    aadhaar_image_back: Optional[str] = None

class WorkerResponse(WorkerBase):
    id: UUID4
    user_id: UUID4
    rating: Decimal
    total_jobs_done: int
    kyc_status: KycStatus
    rejection_reason: Optional[str] = None
    aadhaar_image_front: Optional[str] = None
    aadhaar_image_back: Optional[str] = None
    aadhaar_number: Optional[str] = None

    class Config:
        from_attributes = True

class WorkerDetailedResponse(WorkerResponse):
    user: UserResponse

    class Config:
        from_attributes = True

class WorkerNearbyResponse(WorkerDetailedResponse):
    distance_km: Optional[float] = None

    class Config:
        from_attributes = True

class WorkerStatusUpdate(BaseModel):
    availability_status: AvailabilityStatus
