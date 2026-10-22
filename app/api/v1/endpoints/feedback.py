import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.feedback import (
    CreateFeedbackRequest,
    FeedbackResponse,
    PhotoModerationRequest,
    FeedbackModerationRequest
)
from app.services.feedback_service import (
    submit_feedback,
    get_worker_reviews,
    get_admin_feedbacks,
    toggle_feedback_visibility,
    list_admin_feedback_photos,
    approve_feedback_photo,
    reject_feedback_photo
)

router = APIRouter()
require_admin = deps.RoleChecker(["admin"])

@router.post(
    "/customer/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit review and optional work photos for a worker",
    description="Submits rating, comments, and photos. Automatically credits rating and remark coin rewards (if eligible) and queues photos for admin verification."
)
def create_customer_feedback(
    req: CreateFeedbackRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Submits a review for a worker experience.
    """
    res = submit_feedback(
        db=db,
        customer_user=current_user,
        worker_id=req.worker_id,
        rating=req.rating,
        comments=req.comments,
        photo_urls=req.photo_urls,
        engagement_id=req.engagement_id
    )
    return res

@router.get(
    "/workers/{worker_id}/reviews",
    summary="Get public customer reviews for a worker",
    description="Returns verified customer reviews for a worker profile. Hidden or moderated reviews are omitted."
)
def list_worker_reviews(
    worker_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db)
):
    """
    Public worker reviews listing.
    """
    return get_worker_reviews(
        db=db,
        worker_id=worker_id,
        page=page,
        limit=limit
    )

@router.get(
    "/admin/feedbacks",
    summary="Admin review moderation queue",
    description="Lists all customer reviews with search, ratings, and visibility filter."
)
def list_feedbacks_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    worker_id: Optional[uuid.UUID] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    is_hidden: Optional[bool] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Admin listing of reviews.
    """
    return get_admin_feedbacks(
        db=db,
        page=page,
        limit=limit,
        worker_id=worker_id,
        rating=rating,
        is_hidden=is_hidden
    )

@router.patch(
    "/admin/feedbacks/{id}/toggle-hide",
    summary="Hide or unhide a review",
    description="Toggles the visibility of a customer review without reversing any earned rewards."
)
def toggle_review_hidden_state(
    id: uuid.UUID,
    req: Optional[FeedbackModerationRequest] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Admin toggle review visibility.
    """
    hidden_val = req.is_hidden if req else None
    fb = toggle_feedback_visibility(db=db, feedback_id=id, is_hidden=hidden_val)
    return {
        "id": fb.id,
        "is_hidden": fb.is_hidden,
        "message": f"Review visibility set to {'HIDDEN' if fb.is_hidden else 'VISIBLE'}."
    }

@router.get(
    "/admin/feedback-photos",
    summary="Admin review photo moderation queue",
    description="Lists customer-uploaded work proof photos with status filter (PENDING, APPROVED, REJECTED)."
)
def list_feedback_photos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    List photos awaiting moderation.
    """
    return list_admin_feedback_photos(
        db=db,
        status_filter=status,
        page=page,
        limit=limit
    )

@router.post(
    "/admin/feedback-photos/{id}/approve",
    summary="Approve feedback work photo",
    description="Approves uploaded work photo and credits the configured photo reward to customer's wallet exactly once."
)
def approve_photo(
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Approves photo and awards coins.
    """
    return approve_feedback_photo(
        db=db,
        photo_id=id,
        admin_user=current_user
    )

@router.post(
    "/admin/feedback-photos/{id}/reject",
    summary="Reject feedback work photo",
    description="Rejects uploaded work photo with an optional reason without crediting reward coins."
)
def reject_photo(
    id: uuid.UUID,
    req: Optional[PhotoModerationRequest] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Rejects photo upload.
    """
    reason = req.rejection_reason if req else None
    return reject_feedback_photo(
        db=db,
        photo_id=id,
        admin_user=current_user,
        rejection_reason=reason
    )
