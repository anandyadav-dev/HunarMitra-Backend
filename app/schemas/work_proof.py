from datetime import datetime
from pydantic import UUID4, BaseModel, HttpUrl

class WorkProofBase(BaseModel):
    image_url: str

class WorkProofCreate(WorkProofBase):
    booking_id: UUID4

class WorkProofResponse(WorkProofBase):
    id: UUID4
    booking_id: UUID4
    uploaded_at: datetime

    class Config:
        from_attributes = True
