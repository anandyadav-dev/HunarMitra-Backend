from datetime import date
from decimal import Decimal
from pydantic import UUID4, BaseModel, Field
from typing import Optional, List
from app.models.booking import BookingStatus
from app.schemas.user import UserResponse
from app.schemas.worker import WorkerResponse
from app.schemas.service import ServiceResponse
from app.schemas.work_proof import WorkProofResponse

class BookingBase(BaseModel):
    booking_date: date
    preferred_time: Optional[str] = Field(None, max_length=20)
    address: str

class BookingCreate(BookingBase):
    worker_id: UUID4
    service_id: UUID4

class BookingResponse(BookingBase):
    id: UUID4
    customer_id: UUID4
    worker_id: UUID4
    service_id: UUID4
    status: BookingStatus
    total_amount: Optional[Decimal] = None
    otp_verification: Optional[str] = None

    class Config:
        from_attributes = True

class BookingDetailedResponse(BookingResponse):
    customer: UserResponse
    worker: WorkerResponse
    service: ServiceResponse
    work_proofs: List[WorkProofResponse] = []

    class Config:
        from_attributes = True

class BookingRespond(BaseModel):
    status: BookingStatus = Field(..., description="Must be 'accepted' or 'rejected'")

class BookingComplete(BaseModel):
    total_amount: Decimal = Field(..., gt=0)
    otp: str = Field(..., min_length=6, max_length=6, description="OTP shared by customer to verify completion")
