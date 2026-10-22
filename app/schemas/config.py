from typing import List, Dict, Any
from pydantic import BaseModel
from app.schemas.coin_pack import CoinPackResponse
from app.schemas.reward import RewardResponse

class CoinsConfigResponse(BaseModel):
    contact_unlock_cost: int = 10
    free_contacts_limit: int = 5
    call_unlock_cost: int = 10
    signup_bonus_coins: int = 50
    signup_bonus_enabled: bool = True
    profile_completion_bonus_coins: int = 10
    feedback_reward_coins: int = 5
    feedback_rating_reward_coins: int = 5
    feedback_remark_reward_coins: int = 5
    feedback_photo_reward_coins: int = 10
    min_remark_length: int = 15
    feedback_delay_hours: int = 0
    refund_window_hours: int = 24
    refund_cap_per_month: int = 3
    daily_reward_cap_coins: int = 50
    reveal_rate_limit_per_minute: int = 5
    referral_bonus_coins: int = 25
    daily_contact_limit: int = 20
    min_recharge_coins: int = 50
    coin_to_inr_rate: float = 1.0
    earned_coin_expiry_days: int = 90
    purchased_coin_expiry_days: int = 365
    allow_earned_coins_for_unlock: bool = True
    coin_packs: List[CoinPackResponse] = []
    active_rewards: List[RewardResponse] = []
    all_configs: Dict[str, Any] = {}

    class Config:
        from_attributes = True
