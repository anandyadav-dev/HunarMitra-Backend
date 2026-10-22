from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import UUID4, BaseModel, Field

class CoinPackBase(BaseModel):
    name: str = Field(..., max_length=100, description="Display name of the pack (e.g. '70 Coins Pack')")
    code: str = Field(..., max_length=50, description="Unique code for the pack (e.g. 'pack_70')")
    coins: int = Field(..., gt=0, description="Number of primary coins included")
    bonus_coins: int = Field(0, ge=0, description="Free extra/bonus coins included")
    price_inr: Decimal = Field(..., gt=0, description="Price in INR")
    is_popular: bool = Field(False, description="Whether to highlight as popular")
    badge_text: Optional[str] = Field(None, max_length=50, description="Promotional badge (e.g. 'Most Popular', 'Best Value')")
    description: Optional[str] = Field(None, max_length=255, description="Short pack description")
    sort_order: int = Field(0, ge=0, description="Display sorting order (lowest first)")
    is_active: bool = Field(True, description="Whether this pack is active and purchasable")

class CoinPackCreate(CoinPackBase):
    pass

class CoinPackUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    coins: Optional[int] = Field(None, gt=0)
    bonus_coins: Optional[int] = Field(None, ge=0)
    price_inr: Optional[Decimal] = Field(None, gt=0)
    is_popular: Optional[bool] = None
    badge_text: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class CoinPackResponse(CoinPackBase):
    id: UUID4
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
