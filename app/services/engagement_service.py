import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import distinct
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.engagement import Engagement
from app.models.worker import Worker
from app.models.user import User
from app.models.wallet import Wallet
from app.models.coin_ledger import CoinLedger, CoinAction, CoinType
from app.services.config_service import get_config_value
from app.services.wallet_service import get_or_create_wallet, debit_coins, credit_coins

def get_contact_status(db: Session, customer_user: User, worker_id: uuid.UUID) -> Dict[str, Any]:
    """
    Check reveal status, free contact counts, and unlock cost for a worker contact.
    """
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.is_deleted == False
    ).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
        
    wallet = get_or_create_wallet(db, customer_user.id)
    free_limit = int(get_config_value(db, "free_contacts_limit", 5))
    unlock_cost = int(get_config_value(db, "contact_unlock_cost", 10))
    
    # Check if this worker has already been revealed by this user
    existing_engagement = db.query(Engagement).filter(
        Engagement.user_id == customer_user.id,
        Engagement.worker_id == worker_id,
        Engagement.status != "REFUNDED",
        Engagement.is_deleted == False
    ).order_by(Engagement.created_at.desc()).first()
    
    # Calculate unique workers previously revealed
    unique_revealed_count = db.query(distinct(Engagement.worker_id)).filter(
        Engagement.user_id == customer_user.id,
        Engagement.status != "REFUNDED",
        Engagement.is_deleted == False
    ).count()
    
    free_contacts_used = min(unique_revealed_count, free_limit)
    free_contacts_remaining = max(0, free_limit - unique_revealed_count)
    
    if existing_engagement:
        return {
            "worker_id": worker_id,
            "is_revealed": True,
            "contact_phone": existing_engagement.contact_phone,
            "free_contacts_total": free_limit,
            "free_contacts_used": free_contacts_used,
            "free_contacts_remaining": free_contacts_remaining,
            "coins_required": 0,
            "can_reveal": True,
            "user_total_coins": wallet.total_coins,
            "revealed_at": existing_engagement.created_at,
            "engagement_id": existing_engagement.id
        }
    else:
        coins_required = 0 if free_contacts_remaining > 0 else unlock_cost
        can_reveal = (free_contacts_remaining > 0) or (wallet.total_coins >= coins_required)
        
        return {
            "worker_id": worker_id,
            "is_revealed": False,
            "contact_phone": None,
            "free_contacts_total": free_limit,
            "free_contacts_used": free_contacts_used,
            "free_contacts_remaining": free_contacts_remaining,
            "coins_required": coins_required,
            "can_reveal": can_reveal,
            "user_total_coins": wallet.total_coins,
            "revealed_at": None,
            "engagement_id": None
        }

def reveal_worker_contact(
    db: Session,
    customer_user: User,
    worker_id: uuid.UUID,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reveals a worker's phone number to an authorized customer or contractor.
    - First 5 unique worker contacts are free (0 coins).
    - Subsequent new unique worker contacts deduct 10 coins.
    - Repeated reveals for the same worker are free (idempotent, no double charge).
    - Thread-safe and atomic via row-level wallet lock.
    """
    # 1. Validate worker profile
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.is_deleted == False,
        Worker.is_active == True
    ).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found or currently unavailable."
        )
        
    worker_user = db.query(User).filter(
        User.id == worker.user_id,
        User.is_deleted == False
    ).first()
    if not worker_user or not worker_user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker contact phone number is currently unavailable."
        )
        
    if customer_user.id == worker.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot reveal your own contact information."
        )
        
    # 2. Acquire row-level lock on user wallet for atomic operation
    wallet = db.query(Wallet).filter(
        Wallet.user_id == customer_user.id
    ).with_for_update().first()
    
    if not wallet:
        wallet = get_or_create_wallet(db, customer_user.id)
        wallet = db.query(Wallet).filter(
            Wallet.id == wallet.id
        ).with_for_update().first()
        
    free_limit = int(get_config_value(db, "free_contacts_limit", 5))
    unlock_cost = int(get_config_value(db, "contact_unlock_cost", 10))
    daily_limit = int(get_config_value(db, "daily_contact_limit", 20))
    
    # 3. Check for existing active reveal (Idempotency & No Re-charge)
    existing_engagement = db.query(Engagement).filter(
        Engagement.user_id == customer_user.id,
        Engagement.worker_id == worker_id,
        Engagement.status != "REFUNDED",
        Engagement.is_deleted == False
    ).order_by(Engagement.created_at.desc()).first()
    
    # Calculate unique contacts unlocked
    unique_revealed_count = db.query(distinct(Engagement.worker_id)).filter(
        Engagement.user_id == customer_user.id,
        Engagement.status != "REFUNDED",
        Engagement.is_deleted == False
    ).count()
    
    free_contacts_remaining = max(0, free_limit - unique_revealed_count)
    
    if existing_engagement:
        # Worker already unlocked previously: return immediately with 0 charge
        return {
            "worker_id": worker_id,
            "worker_name": worker_user.full_name or "Skilled Worker",
            "contact_phone": existing_engagement.contact_phone or worker_user.phone_number,
            "engagement_id": existing_engagement.id,
            "is_already_revealed": True,
            "is_free_reveal": (existing_engagement.coins_spent == 0),
            "coins_deducted": 0,
            "remaining_free_contacts": free_contacts_remaining,
            "wallet_balance_coins": wallet.total_coins,
            "revealed_at": existing_engagement.created_at,
            "status": existing_engagement.status
        }
        
    # 4a. Enforce reveal rate limit per minute
    minute_rate_limit = int(get_config_value(db, "reveal_rate_limit_per_minute", 5))
    one_min_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
    recent_reveals_last_min = db.query(Engagement).filter(
        Engagement.user_id == customer_user.id,
        Engagement.created_at >= one_min_ago
    ).count()
    if recent_reveals_last_min >= minute_rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {minute_rate_limit} contact reveals permitted per minute. Please wait a moment."
        )

    # 4b. Enforce daily contact limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_reveals = db.query(Engagement).filter(
        Engagement.user_id == customer_user.id,
        Engagement.created_at >= today_start,
        Engagement.status != "REFUNDED"
    ).count()
    
    if today_reveals >= daily_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily contact reveal limit of {daily_limit} reached. Please try again tomorrow."
        )
        
    # 5. Determine whether free or charged reveal
    coins_to_charge = 0
    is_free = False
    purchased_spent = 0
    earned_spent = 0
    
    if unique_revealed_count < free_limit:
        # User has free reveals available
        is_free = True
        coins_to_charge = 0
        new_free_remaining = max(0, free_limit - (unique_revealed_count + 1))
        
        # Record free ledger audit entry
        ledger_entry = CoinLedger(
            wallet_id=wallet.id,
            user_id=customer_user.id,
            amount=0,
            action=CoinAction.debit.value,
            coin_type=CoinType.earned.value,
            transaction_type="FREE_CONTACT_UNLOCK",
            balance_purchased_after=wallet.purchased_coins,
            balance_earned_after=wallet.earned_coins,
            balance_total_after=wallet.total_coins,
            description=f"Free contact reveal ({unique_revealed_count + 1}/{free_limit}) for {worker_user.full_name or 'Worker'}"
        )
        db.add(ledger_entry)
    else:
        # Free reveals exhausted: deduct 10 coins
        is_free = False
        coins_to_charge = unlock_cost
        new_free_remaining = 0
        
        if wallet.total_coins < coins_to_charge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient coins. You have used your {free_limit} free contacts. Revealing this contact requires {coins_to_charge} coins, but your wallet only has {wallet.total_coins} coins."
            )
            
        # Deduct coins atomically via wallet_service
        txs = debit_coins(
            db=db,
            wallet=wallet,
            amount=coins_to_charge,
            transaction_type="CONTACT_UNLOCK",
            description=f"Contact reveal for {worker_user.full_name or 'Worker'}",
            preferred_source="earned_first"
        )
        
        for tx in txs:
            if tx.coin_type == CoinType.purchased.value:
                purchased_spent += tx.amount
            elif tx.coin_type == CoinType.earned.value:
                earned_spent += tx.amount
                
    # 6. Create Engagement record
    now = datetime.now(timezone.utc)
    engagement = Engagement(
        user_id=customer_user.id,
        worker_id=worker.id,
        engagement_type="CONTACT_UNLOCK",
        coins_spent=coins_to_charge,
        purchased_coins_spent=purchased_spent,
        earned_coins_spent=earned_spent,
        status="ACTIVE",
        contact_phone=worker_user.phone_number,
        created_at=now
    )
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    db.refresh(wallet)
    
    return {
        "worker_id": worker_id,
        "worker_name": worker_user.full_name or "Skilled Worker",
        "contact_phone": worker_user.phone_number,
        "engagement_id": engagement.id,
        "is_already_revealed": False,
        "is_free_reveal": is_free,
        "coins_deducted": coins_to_charge,
        "remaining_free_contacts": new_free_remaining,
        "wallet_balance_coins": wallet.total_coins,
        "revealed_at": engagement.created_at,
        "status": engagement.status
    }

def refund_engagement(
    db: Session,
    customer_user: User,
    engagement_id: uuid.UUID,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Refunds an engagement, restoring spent coins to customer's wallet.
    """
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id,
        Engagement.user_id == customer_user.id
    ).with_for_update().first()
    
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement record not found."
        )
        
    if engagement.status == "REFUNDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contact reveal has already been refunded."
        )
        
    # Check refund window in hours
    refund_window_hours = int(get_config_value(db, "refund_window_hours", 24))
    if refund_window_hours > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=refund_window_hours)
        eng_created = engagement.created_at
        if eng_created.tzinfo is None:
            eng_created = eng_created.replace(tzinfo=timezone.utc)
        if eng_created < cutoff:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund window of {refund_window_hours} hours has expired for this contact reveal."
            )
            
    # Check monthly refund cap
    refund_cap_per_month = int(get_config_value(db, "refund_cap_per_month", 3))
    if refund_cap_per_month > 0:
        first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_refunds = db.query(Engagement).filter(
            Engagement.user_id == customer_user.id,
            Engagement.status == "REFUNDED",
            Engagement.created_at >= first_of_month
        ).count()
        if monthly_refunds >= refund_cap_per_month:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Monthly refund limit of {refund_cap_per_month} reached for this calendar month."
            )

    wallet = db.query(Wallet).filter(
        Wallet.user_id == customer_user.id
    ).with_for_update().first()
    
    total_refunded = engagement.coins_spent
    
    if total_refunded > 0:
        if engagement.purchased_coins_spent > 0:
            credit_coins(
                db=db,
                wallet=wallet,
                amount=engagement.purchased_coins_spent,
                coin_type="purchased",
                transaction_type="REFUND",
                description=f"Refund for contact reveal: {reason or 'Worker unavailable'}",
                reference_id=str(engagement.id)
            )
        if engagement.earned_coins_spent > 0:
            credit_coins(
                db=db,
                wallet=wallet,
                amount=engagement.earned_coins_spent,
                coin_type="earned",
                transaction_type="REFUND",
                description=f"Refund for contact reveal: {reason or 'Worker unavailable'}",
                reference_id=str(engagement.id)
            )
            
    engagement.status = "REFUNDED"
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    db.refresh(wallet)
    
    return {
        "engagement_id": engagement.id,
        "refund_status": "REFUNDED",
        "coins_refunded": total_refunded,
        "message": f"Successfully refunded {total_refunded} coins for this contact reveal." if total_refunded > 0 else "Free contact reveal was cancelled and slot restored.",
        "wallet_balance_coins": wallet.total_coins
    }
