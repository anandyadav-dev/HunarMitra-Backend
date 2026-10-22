from datetime import datetime
from typing import Optional, List
from pydantic import UUID4, BaseModel, Field

class FeedbackPhotoResponse(BaseModel):
    id: UUID4
    photo_url: str
    status: str
    rejection_reason: Optional[str] = None
    reward_granted: bool = False
    reward_coins: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class CreateFeedbackRequest(BaseModel):
    worker_id: UUID4 = Field(..., description="UUID of the worker being reviewed")
    engagement_id: Optional[UUID4] = Field(None, description="UUID of the associated contact unlock engagement")
    rating: int = Field(..., ge=1, le=5, description="Worker rating from 1 to 5 stars")
    comments: Optional[str] = Field(None, description="Optional text feedback or experience description")
    photo_urls: Optional[List[str]] = Field(default_factory=list, description="List of work photos uploaded for admin verification")

class FeedbackResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    user_name: Optional[str] = None
    worker_id: UUID4
    worker_name: Optional[str] = None
    engagement_id: Optional[UUID4] = None
    rating: int
    category: str
    comments: Optional[str] = None
    reward_granted: bool
    reward_coins: int
    is_hidden: bool = False
    created_at: datetime
    photos: List[FeedbackPhotoResponse] = []

    class Config:
        from_attributes = True

class PhotoModerationRequest(BaseModel):
    rejection_reason: Optional[str] = Field(None, description="Reason if photo upload is rejected")

class FeedbackModerationRequest(BaseModel):
    is_hidden: bool = Field(..., description="True to hide review from public view, False to make visible")
