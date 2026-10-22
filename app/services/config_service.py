import json
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from app.models.config import SystemConfig
from app.models.coin_pack import CoinPack
from app.models.reward import Reward

DEFAULT_COIN_CONFIGS: Dict[str, Dict[str, Any]] = {
    "contact_unlock_cost": {
        "value": "10",
        "value_type": "int",
        "category": "coins",
        "description": "Number of coins required to unlock worker contact phone after using free contacts",
        "is_public": True
    },
    "free_contacts_limit": {
        "value": "5",
        "value_type": "int",
        "category": "limits",
        "description": "Number of free unique worker contacts granted to each customer",
        "is_public": True
    },
    "call_unlock_cost": {
        "value": "10",
        "value_type": "int",
        "category": "coins",
        "description": "Number of coins required to initiate direct phone call with worker",
        "is_public": True
    },
    "signup_bonus_coins": {
        "value": "50",
        "value_type": "int",
        "category": "rewards",
        "description": "Free earned coins granted to new first-time customers upon successful registration",
        "is_public": True
    },
    "signup_bonus_enabled": {
        "value": "true",
        "value_type": "bool",
        "category": "rewards",
        "description": "Enable or disable welcome signup bonus coins for new customers",
        "is_public": True
    },
    "profile_completion_bonus_coins": {
        "value": "10",
        "value_type": "int",
        "category": "coins",
        "description": "Coins rewarded for 100% profile completion",
        "is_public": True
    },
    "feedback_reward_coins": {
        "value": "5",
        "value_type": "int",
        "category": "coins",
        "description": "Coins rewarded for submitting feedback on worker or call experience",
        "is_public": True
    },
    "referral_bonus_coins": {
        "value": "25",
        "value_type": "int",
        "category": "coins",
        "description": "Coins awarded to inviter when referral signs up",
        "is_public": True
    },
    "daily_contact_limit": {
        "value": "20",
        "value_type": "int",
        "category": "limits",
        "description": "Maximum number of worker contacts a user can unlock in a single 24-hour window",
        "is_public": True
    },
    "min_recharge_coins": {
        "value": "50",
        "value_type": "int",
        "category": "coins",
        "description": "Minimum coin quantity for custom top-ups",
        "is_public": True
    },
    "coin_to_inr_rate": {
        "value": "1.0",
        "value_type": "float",
        "category": "coins",
        "description": "Nominal exchange rate representing value of 1 coin in INR",
        "is_public": True
    },
    "earned_coin_expiry_days": {
        "value": "90",
        "value_type": "int",
        "category": "coins",
        "description": "Validity period in days for earned/promotional coins before expiration (0 = never)",
        "is_public": True
    },
    "purchased_coin_expiry_days": {
        "value": "365",
        "value_type": "int",
        "category": "coins",
        "description": "Validity period in days for purchased coins before expiration (0 = never)",
        "is_public": True
    },
    "allow_earned_coins_for_unlock": {
        "value": "true",
        "value_type": "bool",
        "category": "coins",
        "description": "Whether earned/bonus coins can be spent on unlocking worker contacts",
        "is_public": True
    },
    "feedback_rating_reward_coins": {
        "value": "2",
        "value_type": "int",
        "category": "rewards",
        "description": "Earned coins rewarded for rating a worker experience (1-5 stars)",
        "is_public": True
    },
    "feedback_remark_reward_coins": {
        "value": "5",
        "value_type": "int",
        "category": "rewards",
        "description": "Earned coins rewarded for writing a detailed feedback remark",
        "is_public": True
    },
    "feedback_photo_reward_coins": {
        "value": "10",
        "value_type": "int",
        "category": "rewards",
        "description": "Earned coins rewarded after admin approves uploaded feedback work photo",
        "is_public": True
    },
    "min_remark_length": {
        "value": "15",
        "value_type": "int",
        "category": "rules",
        "description": "Minimum character length required for feedback text remarks to qualify for bonus coins",
        "is_public": True
    },
    "feedback_delay_hours": {
        "value": "0",
        "value_type": "int",
        "category": "rules",
        "description": "Required delay in hours after revealing contact before feedback can be submitted",
        "is_public": True
    },
    "refund_window_hours": {
        "value": "24",
        "value_type": "int",
        "category": "rules",
        "description": "Maximum hours after contact reveal during which a refund can be requested",
        "is_public": True
    },
    "refund_cap_per_month": {
        "value": "3",
        "value_type": "int",
        "category": "limits",
        "description": "Maximum number of contact reveal refunds permitted per customer per calendar month",
        "is_public": True
    },
    "daily_reward_cap_coins": {
        "value": "50",
        "value_type": "int",
        "category": "limits",
        "description": "Maximum total promotional/reward coins a user can earn in a single day",
        "is_public": True
    },
    "reveal_rate_limit_per_minute": {
        "value": "5",
        "value_type": "int",
        "category": "limits",
        "description": "Maximum number of contact reveal requests permitted per minute",
        "is_public": True
    }
}

def parse_config_value(value_str: str, value_type: str) -> Any:
    """Helper to convert string DB config representation to strongly typed python value."""
    if value_str is None:
        return None
    v_type = value_type.lower()
    if v_type == "int":
        try:
            return int(value_str)
        except (ValueError, TypeError):
            return 0
    elif v_type == "float":
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return 0.0
    elif v_type == "bool":
        return value_str.lower() in ("true", "1", "yes", "t")
    elif v_type == "json":
        try:
            return json.loads(value_str)
        except Exception:
            return {}
    return value_str

def get_config_value(db: Session, key: str, default: Any = None) -> Any:
    """
    Retrieve single config value from DB, falling back to DEFAULT_COIN_CONFIGS or supplied default.
    """
    cfg = db.query(SystemConfig).filter(
        SystemConfig.key == key,
        SystemConfig.is_active == True,
        SystemConfig.is_deleted == False
    ).first()
    
    if cfg:
        return parse_config_value(cfg.value, cfg.value_type)
        
    if key in DEFAULT_COIN_CONFIGS:
        def_item = DEFAULT_COIN_CONFIGS[key]
        return parse_config_value(def_item["value"], def_item["value_type"])
        
    return default

def get_all_configs(db: Session, category: Optional[str] = None, public_only: bool = False) -> Dict[str, Any]:
    """
    Retrieve dictionary of all resolved configurations with defaults.
    """
    result: Dict[str, Any] = {}
    
    # 1. Populate with in-memory defaults
    for k, v in DEFAULT_COIN_CONFIGS.items():
        if category and v.get("category") != category:
            continue
        if public_only and not v.get("is_public", True):
            continue
        result[k] = parse_config_value(v["value"], v["value_type"])
        
    # 2. Override with database records
    query = db.query(SystemConfig).filter(
        SystemConfig.is_active == True,
        SystemConfig.is_deleted == False
    )
    if category:
        query = query.filter(SystemConfig.category == category)
    if public_only:
        query = query.filter(SystemConfig.is_public == True)
        
    db_configs = query.all()
    for row in db_configs:
        result[row.key] = parse_config_value(row.value, row.value_type)
        
    return result

def set_config_value(
    db: Session, 
    key: str, 
    value: Any, 
    value_type: str = "string", 
    category: str = "coins", 
    description: Optional[str] = None,
    is_public: bool = True
) -> SystemConfig:
    """
    Create or update a configuration setting.
    """
    cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    value_str = json.dumps(value) if value_type == "json" else str(value)
    
    if cfg:
        cfg.value = value_str
        cfg.value_type = value_type
        cfg.category = category
        if description:
            cfg.description = description
        cfg.is_public = is_public
        cfg.is_active = True
        cfg.is_deleted = False
    else:
        cfg = SystemConfig(
            key=key,
            value=value_str,
            value_type=value_type,
            category=category,
            description=description,
            is_public=is_public
        )
        db.add(cfg)
        
    db.commit()
    db.refresh(cfg)
    return cfg

def get_coins_config(db: Session) -> Dict[str, Any]:
    """
    Full aggregated coin settings including active coin packs, active rewards, and config limits.
    """
    all_configs = get_all_configs(db, public_only=True)
    
    # Active Coin Packs
    packs = db.query(CoinPack).filter(
        CoinPack.is_active == True,
        CoinPack.is_deleted == False
    ).order_by(CoinPack.sort_order.asc(), CoinPack.coins.asc()).all()
    
    # Active Rewards
    rewards = db.query(Reward).filter(
        Reward.is_active == True,
        Reward.is_deleted == False
    ).all()
    
    return {
        "contact_unlock_cost": int(all_configs.get("contact_unlock_cost", 10)),
        "free_contacts_limit": int(all_configs.get("free_contacts_limit", 5)),
        "call_unlock_cost": int(all_configs.get("call_unlock_cost", 10)),
        "signup_bonus_coins": int(all_configs.get("signup_bonus_coins", 50)),
        "signup_bonus_enabled": bool(all_configs.get("signup_bonus_enabled", True)),
        "profile_completion_bonus_coins": int(all_configs.get("profile_completion_bonus_coins", 10)),
        "feedback_reward_coins": int(all_configs.get("feedback_reward_coins", 5)),
        "feedback_rating_reward_coins": int(all_configs.get("feedback_rating_reward_coins", 5)),
        "feedback_remark_reward_coins": int(all_configs.get("feedback_remark_reward_coins", 5)),
        "feedback_photo_reward_coins": int(all_configs.get("feedback_photo_reward_coins", 10)),
        "min_remark_length": int(all_configs.get("min_remark_length", 15)),
        "feedback_delay_hours": int(all_configs.get("feedback_delay_hours", 0)),
        "refund_window_hours": int(all_configs.get("refund_window_hours", 24)),
        "refund_cap_per_month": int(all_configs.get("refund_cap_per_month", 3)),
        "daily_reward_cap_coins": int(all_configs.get("daily_reward_cap_coins", 50)),
        "reveal_rate_limit_per_minute": int(all_configs.get("reveal_rate_limit_per_minute", 5)),
        "referral_bonus_coins": int(all_configs.get("referral_bonus_coins", 25)),
        "daily_contact_limit": int(all_configs.get("daily_contact_limit", 20)),
        "min_recharge_coins": int(all_configs.get("min_recharge_coins", 50)),
        "coin_to_inr_rate": float(all_configs.get("coin_to_inr_rate", 1.0)),
        "earned_coin_expiry_days": int(all_configs.get("earned_coin_expiry_days", 90)),
        "purchased_coin_expiry_days": int(all_configs.get("purchased_coin_expiry_days", 365)),
        "allow_earned_coins_for_unlock": bool(all_configs.get("allow_earned_coins_for_unlock", True)),
        "coin_packs": packs,
        "active_rewards": rewards,
        "all_configs": all_configs
    }

def list_all_admin_configs(db: Session) -> List[Dict[str, Any]]:
    """
    Returns full list of all system configs with current DB value, defaults, category, and metadata.
    """
    db_configs = {c.key: c for c in db.query(SystemConfig).filter(SystemConfig.is_deleted == False).all()}
    
    result = []
    all_keys = set(DEFAULT_COIN_CONFIGS.keys()).union(set(db_configs.keys()))
    
    for k in sorted(all_keys):
        def_item = DEFAULT_COIN_CONFIGS.get(k, {})
        cfg = db_configs.get(k)
        
        current_str = cfg.value if cfg else def_item.get("value", "")
        v_type = cfg.value_type if cfg else def_item.get("value_type", "string")
        parsed_val = parse_config_value(current_str, v_type)
        
        result.append({
            "key": k,
            "value": parsed_val,
            "raw_value": current_str,
            "value_type": v_type,
            "category": cfg.category if cfg else def_item.get("category", "general"),
            "description": cfg.description if (cfg and cfg.description) else def_item.get("description", ""),
            "is_public": cfg.is_public if cfg else def_item.get("is_public", True),
            "is_customized": cfg is not None
        })
        
    return result

def update_multiple_configs(db: Session, updates: Dict[str, Any]) -> List[SystemConfig]:
    """
    Updates multiple config values with validation.
    """
    from fastapi import HTTPException
    updated_records = []
    for key, val in updates.items():
        v_str = str(val) if val is not None else ""
        def_item = DEFAULT_COIN_CONFIGS.get(key, {})
        v_type = def_item.get("value_type", "string")
        category = def_item.get("category", "general")
        desc = def_item.get("description", "")
        is_pub = def_item.get("is_public", True)
        
        # Validation checks
        if v_type == "int":
            try:
                int_val = int(v_str)
                if int_val < 0:
                    raise ValueError(f"Value for '{key}' cannot be negative.")
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=f"Invalid integer for '{key}': {str(ve)}")
        elif v_type == "float":
            try:
                flt_val = float(v_str)
                if flt_val < 0:
                    raise ValueError(f"Value for '{key}' cannot be negative.")
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=f"Invalid decimal for '{key}': {str(ve)}")
        elif v_type == "bool":
            if isinstance(val, bool):
                v_str = "true" if val else "false"
            else:
                v_str = "true" if str(val).lower() in ("true", "1", "yes") else "false"
                
        record = set_config_value(
            db=db,
            key=key,
            value=v_str,
            value_type=v_type,
            category=category,
            description=desc,
            is_public=is_pub
        )
        updated_records.append(record)
        
    return updated_records
