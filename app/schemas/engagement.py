from datetime import datetime
from typing import Optional
from pydantic import UUID4, BaseModel

class EngagementResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    worker_id: UUID4
    engagement_type: str
    coins_spent: int
    purchased_coins_spent: int
    earned_coins_spent: int
    status: str
    contact_phone: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EngagementCreate(BaseModel):
    worker_id: UUID4
    engagement_type: str = "CONTACT_UNLOCK"
