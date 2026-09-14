from uuid import UUID
import os
import shutil
from decimal import Decimal
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.crud_worker import worker as worker_crud
from app.crud.crud_booking import booking as booking_crud
from app.models.user import User
from app.models.booking import BookingStatus, Booking
from app.models.wallet import Wallet
from app.models.work_proof import WorkProof
from app.models.worker import KycStatus
from app.schemas.worker import WorkerDetailedResponse, WorkerStatusUpdate
from app.schemas.booking import BookingResponse, BookingRespond

router = APIRouter()

UPLOAD_DIR = Path("uploads/work_proofs")

@router.get("/worker/dashboard")
def get_dashboard_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_worker)
):
    """
    Retrieve statistical metrics for the artisan (Earnings, Jobs Completed, Pending Requests).
    """
    worker_profile = worker_crud.get_by_user_id(db, user_id=current_user.id)
    if not worker_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
        
    # Count of completed jobs
    jobs_completed = (
        db.query(Booking)
        .filter(Booking.worker_id == worker_profile.id)
        .filter(Booking.status == BookingStatus.completed)
        .count()
    )
    
    # Count of pending booking requests
    pending_requests = (
        db.query(Booking)
        .filter(Booking.worker_id == worker_profile.id)
        .filter(Booking.status == BookingStatus.pending)
        .count()
    )
    
    # Sum of worker earnings
    total_earnings = (
        db.query(func.sum(Booking.total_amount))
        .filter(Booking.worker_id == worker_profile.id)
        .filter(Booking.status == BookingStatus.completed)
        .scalar()
    ) or Decimal("0.00")
    
    return {
        "earnings": total_earnings,
        "jobs_completed": jobs_completed,
        "pending_requests": pending_requests,
        "availability_status": worker_profile.availability_status
    }

@router.patch("/worker/status", response_model=WorkerDetailedResponse)
def update_status(
    obj_in: WorkerStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_worker)
):
    """
    Toggles the worker's availability status (Online/Offline) to receive nearby jobs.
    """
    worker_profile = worker_crud.get_by_user_id(db, user_id=current_user.id)
    if not worker_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
        
    worker_profile.availability_status = obj_in.availability_status
    db.add(worker_profile)
    db.commit()
    db.refresh(worker_profile)
    return worker_profile

@router.post("/bookings/{id}/respond", response_model=BookingResponse)
def respond_booking(
    id: UUID,
    obj_in: BookingRespond,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_worker)
):
    """
    Accepts or rejects an incoming job request. Transition status: pending -> accepted/rejected.
    """
    worker_profile = worker_crud.get_by_user_id(db, user_id=current_user.id)
    if not worker_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
        
    booking_obj = booking_crud.get(db, id=id)
    if not booking_obj or booking_obj.worker_id != worker_profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking request not found."
        )
        
    if booking_obj.status != BookingStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking has already been responded to."
        )
        
    # Accept or Reject
    booking_obj.status = obj_in.status
    db.add(booking_obj)
    db.commit()
    db.refresh(booking_obj)
    return booking_obj

@router.post("/bookings/{id}/complete", response_model=BookingResponse)
def complete_booking(
    id: UUID,
    total_amount: Decimal = Form(...),
    otp: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_worker)
):
    """
    Finalizes a job booking. Validates the customer-provided OTP, uploads work proof,
    updates stats, and transfers funds between wallets.
    """
    worker_profile = worker_crud.get_by_user_id(db, user_id=current_user.id)
    if not worker_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
        
    booking_obj = booking_crud.get(db, id=id)
    if not booking_obj or booking_obj.worker_id != worker_profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking request not found."
        )
        
    # Accept complete only if accepted (or in progress)
    if booking_obj.status not in [BookingStatus.accepted, BookingStatus.in_progress]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete a booking with status '{booking_obj.status.value}'."
        )
        
    # Verify OTP code
    if booking_obj.otp_verification != otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP verification code. Please request the correct OTP from the customer."
        )
        
    # Finalize invoice amount
    booking_obj.total_amount = total_amount
    booking_obj.status = BookingStatus.completed
    
    # Update worker statistics
    worker_profile.total_jobs_done += 1
    db.add(worker_profile)
    
    # Process wallet payment transfer
    customer_wallet = db.query(Wallet).filter(Wallet.user_id == booking_obj.customer_id).first()
    worker_wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    
    if customer_wallet and worker_wallet:
        customer_wallet.balance -= total_amount
        worker_wallet.balance += total_amount
        db.add(customer_wallet)
        db.add(worker_wallet)
        
    # Save work proof photograph (if uploaded)
    if file:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"booking_{booking_obj.id}_proof{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        work_proof = WorkProof(
            booking_id=booking_obj.id,
            image_url=f"/uploads/work_proofs/{filename}"
        )
        db.add(work_proof)
        
    db.add(booking_obj)
    db.commit()
    db.refresh(booking_obj)
    return booking_obj


@router.post("/worker/kyc", response_model=WorkerDetailedResponse)
def upload_worker_kyc(
    aadhaar_number: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    experience_years: Optional[int] = Form(None),
    pricing_per_hour: Optional[Decimal] = Form(None),
    bio: Optional[str] = Form(None),
    location_lat: Optional[Decimal] = Form(None),
    location_lng: Optional[Decimal] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    aadhaar_image_front: Optional[UploadFile] = File(None),
    aadhaar_image_back: Optional[UploadFile] = File(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_worker)
):
    """
    Submits worker KYC documentation and onboarding details (rates, experience, bio, category, GPS coordinates).
    """
    worker_profile = worker_crud.get_by_user_id(db, user_id=current_user.id)
    if not worker_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found."
        )
        
    kyc_dir = Path("uploads/kyc")
    kyc_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Update Profile Fields (Onboarding details)
    if category:
        worker_profile.category = category.strip()
    if experience_years is not None:
        worker_profile.experience_years = experience_years
    if pricing_per_hour is not None:
        worker_profile.pricing_per_hour = pricing_per_hour
    if bio:
        worker_profile.bio = bio.strip()
    if location_lat is not None:
        worker_profile.location_lat = location_lat
    if location_lng is not None:
        worker_profile.location_lng = location_lng
        
    # 2. Update KYC Documents
    if aadhaar_number:
        # Validate 12-digit clean numeric format
        aadhaar_cleaned = aadhaar_number.strip().replace(" ", "")
        if len(aadhaar_cleaned) != 12 or not aadhaar_cleaned.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aadhaar number must be a valid 12-digit numeric code."
            )
        worker_profile.aadhaar_number = aadhaar_cleaned
        
    if profile_picture:
        ext = os.path.splitext(profile_picture.filename)[1]
        filename = f"worker_{current_user.id}_selfie{ext}"
        path = kyc_dir / filename
        with path.open("wb") as buffer:
            shutil.copyfileobj(profile_picture.file, buffer)
        worker_profile.profile_picture = f"/uploads/kyc/{filename}"
        
    if aadhaar_image_front:
        ext = os.path.splitext(aadhaar_image_front.filename)[1]
        filename = f"worker_{current_user.id}_aadhaar_front{ext}"
        path = kyc_dir / filename
        with path.open("wb") as buffer:
            shutil.copyfileobj(aadhaar_image_front.file, buffer)
        worker_profile.aadhaar_image_front = f"/uploads/kyc/{filename}"
        
    if aadhaar_image_back:
        ext = os.path.splitext(aadhaar_image_back.filename)[1]
        filename = f"worker_{current_user.id}_aadhaar_back{ext}"
        path = kyc_dir / filename
        with path.open("wb") as buffer:
            shutil.copyfileobj(aadhaar_image_back.file, buffer)
        worker_profile.aadhaar_image_back = f"/uploads/kyc/{filename}"
        
    # Queue for review
    worker_profile.kyc_status = KycStatus.pending
    worker_profile.rejection_reason = None
    
    db.add(worker_profile)
    db.commit()
    db.refresh(worker_profile)
    return worker_profile
