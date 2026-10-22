from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import UUID4, BaseModel, Field

class CoinLedgerResponse(BaseModel):
    id: UUID4
    wallet_id: UUID4
    user_id: UUID4
    amount: int
    action: str
    coin_type: str
    transaction_type: str
    balance_purchased_after: int
    balance_earned_after: int
    balance_total_after: int
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WalletBase(BaseModel):
    balance: Decimal = Field(..., ge=0)

class WalletResponse(WalletBase):
    id: UUID4
    user_id: UUID4
    purchased_coins: int = 0
    earned_coins: int = 0
    total_coins: int = 0
    last_updated: datetime
    recent_transactions: Optional[List[CoinLedgerResponse]] = None

    class Config:
        from_attributes = True

class WalletDeposit(BaseModel):
    amount: Decimal = Field(..., gt=0)
