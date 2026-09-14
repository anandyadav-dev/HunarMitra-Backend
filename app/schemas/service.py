from decimal import Decimal
from pydantic import UUID4, BaseModel, Field
from typing import Optional

class ServiceBase(BaseModel):
    name: str = Field(..., max_length=50)
    icon_url: Optional[str] = Field(None, max_length=255)
    base_price: Decimal = Field(..., ge=0)

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    icon_url: Optional[str] = Field(None, max_length=255)
    base_price: Optional[Decimal] = Field(None, ge=0)

class ServiceResponse(ServiceBase):
    id: UUID4

    class Config:
        from_attributes = True
