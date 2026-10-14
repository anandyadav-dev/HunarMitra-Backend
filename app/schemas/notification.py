from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    message: str

class NotificationCreate(NotificationBase):
    user_id: uuid.UUID

class NotificationResponse(NotificationBase):
    id: uuid.UUID
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
