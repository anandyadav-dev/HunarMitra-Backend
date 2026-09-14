from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.crud_worker import worker as worker_crud
from app.crud.crud_booking import booking as booking_crud
from app.models.user import User
from app.models.service import Service
from app.schemas.worker import WorkerNearbyResponse, WorkerDetailedResponse
from app.schemas.booking import BookingCreate, BookingResponse, BookingDetailedResponse

router = APIRouter()

@router.get("/workers/nearby", response_model=List[WorkerNearbyResponse])
def get_nearby_workers(
    lat: float = Query(..., description="Latitude of user's current location"),
    lng: float = Query(..., description="Longitude of user's current location"),
    category: Optional[str] = Query(None, description="Category of worker (e.g. Plumber, Electrician)"),
    radius_km: float = Query(10.0, description="Radius within which to search, in kilometers"),
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

@router.get("/workers/{id}", response_model=WorkerDetailedResponse)
def get_worker_profile(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Gets detailed profile information for a specific worker. Accessible by all authenticated users.
    """
    worker_obj = worker_crud.get(db, id=id)
    if not worker_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
    return worker_obj

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
