from datetime import datetime
from typing import Optional
from pydantic import UUID4, BaseModel

class RewardResponse(BaseModel):
    id: UUID4
    reward_code: str
    title: str
    description: Optional[str] = None
    coins_amount: int
    max_claims_per_user: int = 1
    valid_until: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class UserRewardResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    reward_id: Optional[UUID4] = None
    reward_code: str
    coins_awarded: int
    reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
