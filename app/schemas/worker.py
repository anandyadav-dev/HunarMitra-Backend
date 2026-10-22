from decimal import Decimal
from pydantic import UUID4, BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserResponse, UserPublicResponse
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
    additional_skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None

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
    additional_skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
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
    user: UserPublicResponse

    class Config:
        from_attributes = True

class WorkerNearbyResponse(WorkerDetailedResponse):
    distance_km: Optional[float] = None

    class Config:
        from_attributes = True

class WorkerStatusUpdate(BaseModel):
    availability_status: AvailabilityStatus

class WorkerRevealRequest(BaseModel):
    idempotency_key: Optional[str] = None

class WorkerRevealResponse(BaseModel):
    worker_id: UUID4
    worker_name: str
    contact_phone: str
    engagement_id: UUID4
    is_already_revealed: bool
    is_free_reveal: bool
    coins_deducted: int
    remaining_free_contacts: int
    wallet_balance_coins: int
    revealed_at: datetime
    status: str

    class Config:
        from_attributes = True

class ContactStatusResponse(BaseModel):
    worker_id: UUID4
    is_revealed: bool
    contact_phone: Optional[str] = None
    free_contacts_total: int
    free_contacts_used: int
    free_contacts_remaining: int
    coins_required: int
    can_reveal: bool
    user_total_coins: int
    revealed_at: Optional[datetime] = None
    engagement_id: Optional[UUID4] = None

    class Config:
        from_attributes = True

class EngagementRefundResponse(BaseModel):
    engagement_id: UUID4
    refund_status: str
    coins_refunded: int
    message: str
    wallet_balance_coins: int

    class Config:
        from_attributes = True
