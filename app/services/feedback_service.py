import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from app.models.feedback import Feedback
from app.models.feedback_photo import FeedbackPhoto, PhotoReviewStatus
from app.models.engagement import Engagement
from app.models.worker import Worker
from app.models.user import User
from app.models.wallet import Wallet
from app.models.coin_ledger import CoinLedger, CoinAction, CoinType
from app.services.config_service import get_config_value
from app.services.wallet_service import get_or_create_wallet, credit_coins

def submit_feedback(
    db: Session,
    customer_user: User,
    worker_id: uuid.UUID,
    rating: int,
    comments: Optional[str] = None,
    photo_urls: Optional[List[str]] = None,
    engagement_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Submits feedback and review for a worker experience.
    - Validates rating (1 to 5).
    - Prevents duplicate feedback rewards for the same engagement.
    - Honors feedback delay (if configured).
    - Awards rating bonus coins and remark bonus coins (if min length met and within daily cap).
    - Uploaded photos enter moderation queue with PENDING status.
    """
    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be an integer between 1 and 5."
        )

    # 1. Validate worker profile
    worker = db.query(Worker).filter(Worker.id == worker_id, Worker.is_deleted == False).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )

    if customer_user.id == worker.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot submit feedback for your own profile."
        )

    # 2. Validate engagement if provided
    engagement = None
    if engagement_id:
        engagement = db.query(Engagement).filter(
            Engagement.id == engagement_id,
            Engagement.user_id == customer_user.id
        ).first()
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement record not found or does not belong to you."
            )

        # Enforce feedback delay if configured
        feedback_delay_hours = int(get_config_value(db, "feedback_delay_hours", 0))
        if feedback_delay_hours > 0:
            eng_created = engagement.created_at
            if eng_created.tzinfo is None:
                eng_created = eng_created.replace(tzinfo=timezone.utc)
            min_eligible_time = eng_created + timedelta(hours=feedback_delay_hours)
            if datetime.now(timezone.utc) < min_eligible_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feedback can only be submitted {feedback_delay_hours} hours after revealing contact."
                )

    # 3. Prevent duplicate reward for the same engagement
    already_rewarded = False
    if engagement_id:
        existing_fb = db.query(Feedback).filter(
            Feedback.user_id == customer_user.id,
            Feedback.engagement_id == engagement_id,
            Feedback.reward_granted == True
        ).first()
        if existing_fb:
            already_rewarded = True

    # 4. Calculate earned coin rewards
    rating_reward = int(get_config_value(db, "feedback_rating_reward_coins", 2))
    remark_reward = int(get_config_value(db, "feedback_remark_reward_coins", 5))
    min_remark_len = int(get_config_value(db, "min_remark_length", 15))
    daily_reward_cap = int(get_config_value(db, "daily_reward_cap_coins", 50))

    coins_to_award = 0
    if not already_rewarded:
        coins_to_award += rating_reward
        if comments and len(comments.strip()) >= min_remark_len:
            coins_to_award += remark_reward

        # Check daily reward cap
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_earned_today = db.query(func.coalesce(func.sum(CoinLedger.amount), 0)).filter(
            CoinLedger.user_id == customer_user.id,
            CoinLedger.action == CoinAction.credit.value,
            CoinLedger.coin_type == CoinType.earned.value,
            CoinLedger.created_at >= today_start
        ).scalar() or 0

        remaining_cap = max(0, daily_reward_cap - daily_earned_today)
        coins_to_award = min(coins_to_award, remaining_cap)

    # 5. Create Feedback record
    now = datetime.now(timezone.utc)
    new_feedback = Feedback(
        user_id=customer_user.id,
        worker_id=worker.id,
        engagement_id=engagement_id,
        rating=rating,
        category="WORKER_EXPERIENCE",
        comments=comments.strip() if comments else None,
        reward_granted=(coins_to_award > 0),
        reward_coins=coins_to_award,
        is_hidden=False,
        created_at=now
    )
    db.add(new_feedback)
    db.flush()

    # 6. Credit earned coins if awarded
    if coins_to_award > 0:
        wallet = get_or_create_wallet(db, customer_user.id)
        credit_coins(
            db=db,
            wallet=wallet,
            amount=coins_to_award,
            coin_type="earned",
            transaction_type="FEEDBACK_REWARD",
            reference_id=str(new_feedback.id),
            description=f"Feedback reward ({rating}★ review)"
        )

    # 7. Attach photos in PENDING status for moderation
    created_photos = []
    if photo_urls:
        for url in photo_urls:
            clean_url = url.strip()
            if clean_url:
                p = FeedbackPhoto(
                    feedback_id=new_feedback.id,
                    user_id=customer_user.id,
                    photo_url=clean_url,
                    status=PhotoReviewStatus.pending.value,
                    reward_granted=False,
                    reward_coins=0,
                    created_at=now
                )
                db.add(p)
                created_photos.append(p)

    db.commit()
    db.refresh(new_feedback)

    return {
        "id": new_feedback.id,
        "user_id": new_feedback.user_id,
        "user_name": customer_user.full_name,
        "worker_id": new_feedback.worker_id,
        "worker_name": worker.user.full_name if (worker and worker.user) else None,
        "engagement_id": new_feedback.engagement_id,
        "rating": new_feedback.rating,
        "category": new_feedback.category or "WORKER_EXPERIENCE",
        "comments": new_feedback.comments,
        "reward_granted": new_feedback.reward_granted,
        "reward_coins": new_feedback.reward_coins,
        "is_hidden": new_feedback.is_hidden,
        "created_at": new_feedback.created_at,
        "photos": [
            {
                "id": ph.id,
                "photo_url": ph.photo_url,
                "status": ph.status,
                "rejection_reason": ph.rejection_reason,
                "reward_granted": ph.reward_granted,
                "reward_coins": ph.reward_coins,
                "created_at": ph.created_at
            }
            for ph in created_photos
        ]
    }

def get_worker_reviews(
    db: Session,
    worker_id: uuid.UUID,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Returns public reviews for a worker, strictly excluding hidden or soft-deleted reviews.
    """
    query = db.query(Feedback).filter(
        Feedback.worker_id == worker_id,
        Feedback.is_hidden == False,
        Feedback.is_deleted == False
    )
    total = query.count()
    offset = (page - 1) * limit
    reviews = query.order_by(desc(Feedback.created_at)).offset(offset).limit(limit).all()

    items = []
    for r in reviews:
        photos = db.query(FeedbackPhoto).filter(
            FeedbackPhoto.feedback_id == r.id,
            FeedbackPhoto.status == PhotoReviewStatus.approved.value,
            FeedbackPhoto.is_deleted == False
        ).all()
        user_name = r.user.full_name if r.user else "Verified Customer"
        items.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": user_name,
            "worker_id": r.worker_id,
            "rating": r.rating,
            "comments": r.comments,
            "created_at": r.created_at,
            "photos": [
                {
                    "id": p.id,
                    "photo_url": p.photo_url,
                    "status": p.status,
                    "created_at": p.created_at
                }
                for p in photos
            ]
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }

def get_admin_feedbacks(
    db: Session,
    page: int = 1,
    limit: int = 20,
    worker_id: Optional[uuid.UUID] = None,
    rating: Optional[int] = None,
    is_hidden: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Admin listing of reviews with search, ratings, moderation filters, and attached photos.
    """
    query = db.query(Feedback).filter(Feedback.is_deleted == False)
    if worker_id:
        query = query.filter(Feedback.worker_id == worker_id)
    if rating:
        query = query.filter(Feedback.rating == rating)
    if is_hidden is not None:
        query = query.filter(Feedback.is_hidden == is_hidden)

    total = query.count()
    offset = (page - 1) * limit
    feedbacks = query.order_by(desc(Feedback.created_at)).offset(offset).limit(limit).all()

    items = []
    for fb in feedbacks:
        photos = db.query(FeedbackPhoto).filter(
            FeedbackPhoto.feedback_id == fb.id,
            FeedbackPhoto.is_deleted == False
        ).all()
        items.append({
            "id": fb.id,
            "user_id": fb.user_id,
            "user_name": fb.user.full_name if fb.user else "Customer",
            "user_phone": fb.user.phone_number if fb.user else None,
            "worker_id": fb.worker_id,
            "worker_name": fb.worker.user.full_name if (fb.worker and fb.worker.user) else "Worker",
            "engagement_id": fb.engagement_id,
            "rating": fb.rating,
            "comments": fb.comments,
            "reward_granted": fb.reward_granted,
            "reward_coins": fb.reward_coins,
            "is_hidden": fb.is_hidden,
            "created_at": fb.created_at,
            "photos": [
                {
                    "id": p.id,
                    "photo_url": p.photo_url,
                    "status": p.status,
                    "rejection_reason": p.rejection_reason,
                    "reward_granted": p.reward_granted,
                    "reward_coins": p.reward_coins,
                    "created_at": p.created_at
                }
                for p in photos
            ]
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1,
        "items": items
    }

def toggle_feedback_visibility(
    db: Session,
    feedback_id: uuid.UUID,
    is_hidden: Optional[bool] = None
) -> Feedback:
    """
    Hides or unhides a review from public listing without reversing earned rewards.
    """
    fb = db.get(Feedback, feedback_id)
    if not fb or fb.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found.")

    if is_hidden is None:
        fb.is_hidden = not fb.is_hidden
    else:
        fb.is_hidden = is_hidden

    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb

def list_admin_feedback_photos(
    db: Session,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Admin photo review queue for feedback work proof photos.
    """
    query = db.query(FeedbackPhoto).filter(FeedbackPhoto.is_deleted == False)
    if status_filter:
        query = query.filter(FeedbackPhoto.status == status_filter.upper())

    total = query.count()
    offset = (page - 1) * limit
    photos = query.order_by(desc(FeedbackPhoto.created_at)).offset(offset).limit(limit).all()

    items = []
    for p in photos:
        items.append({
            "id": p.id,
            "feedback_id": p.feedback_id,
            "user_id": p.user_id,
            "user_name": p.user.full_name if p.user else "Customer",
            "photo_url": p.photo_url,
            "status": p.status,
            "rejection_reason": p.rejection_reason,
            "reward_granted": p.reward_granted,
            "reward_coins": p.reward_coins,
            "reviewed_by": p.reviewed_by,
            "reviewed_at": p.reviewed_at,
            "created_at": p.created_at
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1,
        "items": items
    }

def approve_feedback_photo(
    db: Session,
    photo_id: uuid.UUID,
    admin_user: User
) -> Dict[str, Any]:
    """
    Approves a feedback photo and credits photo reward coins exactly once (idempotent).
    """
    photo = db.query(FeedbackPhoto).filter(
        FeedbackPhoto.id == photo_id
    ).with_for_update().first()

    if not photo or photo.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback photo not found.")

    if photo.status == PhotoReviewStatus.approved.value and photo.reward_granted:
        return {
            "id": photo.id,
            "status": photo.status,
            "reward_granted": True,
            "reward_coins": photo.reward_coins,
            "message": "Photo was already approved and reward was credited."
        }

    now = datetime.now(timezone.utc)
    photo_reward = int(get_config_value(db, "feedback_photo_reward_coins", 10))

    wallet = get_or_create_wallet(db, photo.user_id)
    wallet = db.query(Wallet).filter(Wallet.id == wallet.id).with_for_update().first()

    if not photo.reward_granted and photo_reward > 0:
        credit_coins(
            db=db,
            wallet=wallet,
            amount=photo_reward,
            coin_type="earned",
            transaction_type="PHOTO_REWARD",
            reference_id=str(photo.id),
            description="Bonus reward for verified work proof photo"
        )
        photo.reward_granted = True
        photo.reward_coins = photo_reward

    photo.status = PhotoReviewStatus.approved.value
    photo.rejection_reason = None
    photo.reviewed_by = admin_user.id
    photo.reviewed_at = now

    db.add(photo)
    db.commit()
    db.refresh(photo)

    return {
        "id": photo.id,
        "status": photo.status,
        "reward_granted": photo.reward_granted,
        "reward_coins": photo.reward_coins,
        "message": f"Photo approved successfully. {photo.reward_coins} coins credited to customer wallet."
    }

def reject_feedback_photo(
    db: Session,
    photo_id: uuid.UUID,
    admin_user: User,
    rejection_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rejects a feedback photo without crediting reward coins.
    """
    photo = db.query(FeedbackPhoto).filter(
        FeedbackPhoto.id == photo_id
    ).with_for_update().first()

    if not photo or photo.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback photo not found.")

    photo.status = PhotoReviewStatus.rejected.value
    photo.rejection_reason = rejection_reason.strip() if rejection_reason else "Photo does not meet verification guidelines"
    photo.reviewed_by = admin_user.id
    photo.reviewed_at = datetime.now(timezone.utc)

    db.add(photo)
    db.commit()
    db.refresh(photo)

    return {
        "id": photo.id,
        "status": photo.status,
        "rejection_reason": photo.rejection_reason,
        "reward_granted": False,
        "reward_coins": 0,
        "message": "Photo rejected."
    }
