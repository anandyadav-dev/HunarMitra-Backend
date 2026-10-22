import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.wallet import Wallet
from app.models.coin_ledger import CoinLedger, CoinType, CoinAction
from app.models.user import User
from app.services.config_service import get_config_value

def award_signup_reward(db: Session, user_id: uuid.UUID) -> Optional[CoinLedger]:
    """
    Credits first-time customer signup bonus coins to the user's wallet.
    Idempotent and atomic: guarantees the reward is credited strictly once per customer.
    """
    # 1. Check configuration
    is_enabled = bool(get_config_value(db, "signup_bonus_enabled", True))
    bonus_coins = int(get_config_value(db, "signup_bonus_coins", 50))
    if not is_enabled or bonus_coins <= 0:
        return None

    # 2. Check user role
    user = db.get(User, user_id)
    if not user:
        return None
    
    # Check if user has customer role (default is customer if roles not specified)
    is_customer = True
    if user.roles:
        role_names = [r.name.lower() for r in user.roles]
        is_customer = "customer" in role_names
    
    if not is_customer:
        return None

    # 3. Lock wallet row or create if not exists
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).with_for_update().first()
    if not wallet:
        wallet = Wallet(
            user_id=user_id,
            balance=Decimal("0.00"),
            purchased_coins=0,
            earned_coins=0
        )
        db.add(wallet)
        db.flush()

    # 4. Check idempotency: has a SIGNUP_BONUS credit already been recorded for this user?
    existing_bonus = db.query(CoinLedger).filter(
        CoinLedger.user_id == user_id,
        CoinLedger.transaction_type == "SIGNUP_BONUS",
        CoinLedger.action == CoinAction.credit.value
    ).first()
    if existing_bonus:
        return None  # Already awarded, prevent duplicate reward

    # 5. Atomically credit the reward
    wallet.earned_coins += bonus_coins
    
    ledger_entry = CoinLedger(
        wallet_id=wallet.id,
        user_id=user_id,
        amount=bonus_coins,
        action=CoinAction.credit.value,
        coin_type=CoinType.earned.value,
        transaction_type="SIGNUP_BONUS",
        balance_purchased_after=wallet.purchased_coins,
        balance_earned_after=wallet.earned_coins,
        balance_total_after=wallet.total_coins,
        description="Signup Bonus"
    )
    db.add(wallet)
    db.add(ledger_entry)
    db.commit()
    db.refresh(wallet)
    db.refresh(ledger_entry)
    return ledger_entry

def get_or_create_wallet(db: Session, user_id: uuid.UUID) -> Wallet:
    """
    Retrieve user wallet or initialize a new one with configurable signup bonus coins.
    """
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(
            user_id=user_id,
            balance=Decimal("0.00"),
            purchased_coins=0,
            earned_coins=0
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        
    # Award signup reward if eligible and not already awarded (idempotent)
    award_signup_reward(db, user_id)
    db.refresh(wallet)
    return wallet

def credit_coins(
    db: Session,
    wallet: Wallet,
    amount: int,
    coin_type: str = "earned",
    transaction_type: str = "BONUS",
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
    metadata_json: Optional[dict] = None
) -> CoinLedger:
    """
    Credits coins to either the purchased or earned bucket and records a ledger transaction.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit amount must be greater than zero."
        )
        
    coin_type_normalized = coin_type.lower()
    if coin_type_normalized == CoinType.purchased.value:
        wallet.purchased_coins += amount
    elif coin_type_normalized == CoinType.earned.value:
        wallet.earned_coins += amount
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid coin_type '{coin_type}'. Must be 'purchased' or 'earned'."
        )
        
    ledger_entry = CoinLedger(
        wallet_id=wallet.id,
        user_id=wallet.user_id,
        amount=amount,
        action=CoinAction.credit.value,
        coin_type=coin_type_normalized,
        transaction_type=transaction_type,
        balance_purchased_after=wallet.purchased_coins,
        balance_earned_after=wallet.earned_coins,
        balance_total_after=wallet.total_coins,
        reference_id=reference_id,
        description=description,
        metadata_json=metadata_json
    )
    
    db.add(wallet)
    db.add(ledger_entry)
    db.commit()
    db.refresh(wallet)
    db.refresh(ledger_entry)
    
    return ledger_entry

def debit_coins(
    db: Session,
    wallet: Wallet,
    amount: int,
    transaction_type: str = "ENGAGEMENT_UNLOCK",
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
    metadata_json: Optional[dict] = None,
    preferred_source: str = "earned_first"
) -> List[CoinLedger]:
    """
    Debits coins, honoring separate purchased vs earned coin pools.
    By default, uses earned/promotional coins first, followed by purchased coins.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debit amount must be greater than zero."
        )
        
    if wallet.total_coins < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient coin balance. Required: {amount}, Available: {wallet.total_coins}."
        )
        
    ledger_entries: List[CoinLedger] = []
    
    # Calculate split between earned and purchased coins
    if preferred_source == "earned_first":
        earned_deduct = min(wallet.earned_coins, amount)
        purchased_deduct = amount - earned_deduct
    else:
        purchased_deduct = min(wallet.purchased_coins, amount)
        earned_deduct = amount - purchased_deduct
        
    # Deduct earned coins if needed
    if earned_deduct > 0:
        wallet.earned_coins -= earned_deduct
        entry = CoinLedger(
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            amount=earned_deduct,
            action=CoinAction.debit.value,
            coin_type=CoinType.earned.value,
            transaction_type=transaction_type,
            balance_purchased_after=wallet.purchased_coins,
            balance_earned_after=wallet.earned_coins,
            balance_total_after=wallet.total_coins,
            reference_id=reference_id,
            description=description,
            metadata_json=metadata_json
        )
        db.add(entry)
        ledger_entries.append(entry)
        
    # Deduct purchased coins if needed
    if purchased_deduct > 0:
        wallet.purchased_coins -= purchased_deduct
        entry = CoinLedger(
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            amount=purchased_deduct,
            action=CoinAction.debit.value,
            coin_type=CoinType.purchased.value,
            transaction_type=transaction_type,
            balance_purchased_after=wallet.purchased_coins,
            balance_earned_after=wallet.earned_coins,
            balance_total_after=wallet.total_coins,
            reference_id=reference_id,
            description=description,
            metadata_json=metadata_json
        )
        db.add(entry)
        ledger_entries.append(entry)
        
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    for e in ledger_entries:
        db.refresh(e)
        
    return ledger_entries

def get_recent_transactions(db: Session, wallet_id: uuid.UUID, limit: int = 20) -> List[CoinLedger]:
    """Retrieve recent coin transactions for a given wallet."""
    return db.query(CoinLedger).filter(
        CoinLedger.wallet_id == wallet_id
    ).order_by(CoinLedger.created_at.desc()).limit(limit).all()
