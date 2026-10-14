import datetime
import uuid
from typing import Optional
from pydantic import BaseModel

class LegalDocumentBase(BaseModel):
    title: str
    slug: str
    content: str

class LegalDocumentCreate(BaseModel):
    title: str
    slug: str
    content: str

class LegalDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class LegalDocumentResponse(LegalDocumentBase):
    id: uuid.UUID
    is_active: bool
    is_deleted: bool
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
