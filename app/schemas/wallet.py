from datetime import datetime
from decimal import Decimal
from pydantic import UUID4, BaseModel, Field

class WalletBase(BaseModel):
    balance: Decimal = Field(..., ge=0)

class WalletResponse(WalletBase):
    id: UUID4
    user_id: UUID4
    last_updated: datetime

    class Config:
        from_attributes = True

class WalletDeposit(BaseModel):
    amount: Decimal = Field(..., gt=0)
