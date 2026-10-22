from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api import deps
from app.crud.crud_worker import worker as worker_crud
from app.crud.crud_booking import booking as booking_crud
from app.models.user import User
from app.models.worker import Worker
from app.models.service import Service
from app.schemas.worker import (
    WorkerNearbyResponse, 
    WorkerDetailedResponse,
    WorkerRevealRequest,
    WorkerRevealResponse,
    ContactStatusResponse,
    EngagementRefundResponse
)
from app.schemas.booking import BookingCreate, BookingResponse, BookingDetailedResponse
from app.services.engagement_service import (
    get_contact_status,
    reveal_worker_contact,
    refund_engagement
)

router = APIRouter()

@router.get(
    "/workers",
    response_model=List[WorkerDetailedResponse],
    summary="List and search workers",
    description="Lists active workers with filtering by category, city, or search term. Never returns worker phone numbers."
)
def list_workers(
    category: Optional[str] = Query(None, description="Filter by category (e.g. Plumber, Electrician)"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    search: Optional[str] = Query(None, description="Search by name, skill, or bio"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Search and browse available workers. Sensitive contact information (phone number) is excluded.
    """
    query = db.query(Worker).join(User, Worker.user_id == User.id).filter(
        Worker.is_deleted == False,
        Worker.is_active == True,
        User.is_deleted == False
    )
    
    if category:
        query = query.filter(Worker.category.ilike(f"%{category.strip()}%"))
        
    if city:
        query = query.filter(or_(Worker.city.ilike(f"%{city.strip()}%"), User.city.ilike(f"%{city.strip()}%")))
        
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(s),
                Worker.category.ilike(s),
                Worker.bio.ilike(s)
            )
        )
        
    workers = query.order_by(Worker.rating.desc(), Worker.total_jobs_done.desc()).offset(skip).limit(limit).all()
    return workers

@router.get(
    "/workers/nearby", 
    response_model=List[WorkerNearbyResponse],
    summary="List nearby online workers",
    description="Lists online workers matching category within a distance radius. Never returns worker phone numbers."
)
def get_nearby_workers(
    lat: float = Query(..., description="Latitude of user's current location"),
    lng: float = Query(..., description="Longitude of user's current location"),
    category: Optional[str] = Query(None, description="Category of worker (e.g. Plumber, Electrician)"),
    radius_km: float = Query(100.0, description="Radius within which to search, in kilometers"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_customer)
):
    """
    Lists online workers matching the category within a distance radius. Requires customer authentication.
    """
    workers = worker_crud.get_nearby_workers(
        db, category=category, lat=lat, lng=lng, radius_km=radius_km
    )
    return workers

@router.get(
    "/workers/{id}", 
    response_model=WorkerDetailedResponse,
    summary="Get worker profile details",
    description="Gets detailed public profile information for a worker. Phone number is excluded; use the reveal API to unlock contact."
)
def get_worker_profile(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Gets detailed profile information for a specific worker. Accessible by all authenticated users.
    Phone numbers are strictly omitted and must be requested via POST /workers/{id}/reveal.
    """
    worker_obj = worker_crud.get(db, id=id)
    if not worker_obj or worker_obj.is_deleted or not worker_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
    return worker_obj

@router.get(
    "/workers/{id}/contact-status",
    response_model=ContactStatusResponse,
    summary="Check contact reveal status and coin cost",
    description="Returns whether the worker contact has already been revealed, free contacts remaining, and coins required to unlock."
)
def check_worker_contact_status(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Check if the authenticated user has unlocked this worker's phone number,
    how many free contacts remain, and how many coins are required.
    """
    return get_contact_status(db, customer_user=current_user, worker_id=id)

@router.post(
    "/workers/{id}/reveal",
    response_model=WorkerRevealResponse,
    summary="Authorize and reveal worker contact phone",
    description="Unlocks and returns the worker's phone number. First 5 unique worker contacts are free, then 10 coins per new contact. Repeated reveals do not charge."
)
def reveal_worker_phone(
    id: UUID,
    req_body: Optional[WorkerRevealRequest] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Authorized contact reveal:
    - 5 free unique worker contacts per customer
    - 10 coins per new unique contact afterwards
    - Repeated reveals for the same worker are free
    - Thread-safe atomic transactions and idempotency
    """
    eff_key = idempotency_key or (req_body.idempotency_key if req_body else None)
    return reveal_worker_contact(db, customer_user=current_user, worker_id=id, idempotency_key=eff_key)

@router.post(
    "/engagements/{id}/refund",
    response_model=EngagementRefundResponse,
    summary="Refund a contact reveal engagement",
    description="Refunds coins spent for a contact reveal if worker was unreachable or unavailable."
)
def refund_reveal(
    id: UUID,
    reason: Optional[str] = Query(None, description="Reason for refund request"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Refunds spent coins for an engagement back to the customer's wallet.
    """
    return refund_engagement(db, customer_user=current_user, engagement_id=id, reason=reason)

@router.post("/bookings/create", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    obj_in: BookingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_customer)
):
    """
    Creates a new job booking request. Automatically generates a 6-digit OTP verification code.
    """
    worker_obj = worker_crud.get(db, id=obj_in.worker_id)
    if not worker_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
        
    service_obj = db.get(Service, obj_in.service_id)
    if not service_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service category not found."
        )
        
    new_booking = booking_crud.create_with_otp(db, obj_in=obj_in, customer_id=current_user.id)
    return new_booking

@router.get("/bookings/my-history", response_model=List[BookingDetailedResponse])
def get_my_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_customer)
):
    """
    Lists booking history for the authenticated customer.
    """
    bookings = booking_crud.get_by_customer(
        db, customer_id=current_user.id, skip=skip, limit=limit
    )
    return bookings
