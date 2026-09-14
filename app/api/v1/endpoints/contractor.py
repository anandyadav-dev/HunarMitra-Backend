import os
import shutil
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.contractor import Contractor
from app.models.worker import KycStatus
from app.schemas.contractor import ContractorDetailedResponse

router = APIRouter()

@router.post("/contractor/kyc", response_model=ContractorDetailedResponse)
def upload_contractor_kyc(
    company_name: Optional[str] = Form(None),
    gst_number: Optional[str] = Form(None),
    pan_number: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    business_license: Optional[UploadFile] = File(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_contractor)
):
    """
    Submits contractor KYC documentation and business profile details (license, PAN, GSTIN, company logo).
    """
    contractor_profile = db.query(Contractor).filter(Contractor.user_id == current_user.id).first()
    if not contractor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor profile not found."
        )
        
    kyc_dir = Path("uploads/kyc")
    kyc_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Update Profile Fields (Onboarding details)
    if company_name:
        contractor_profile.company_name = company_name.strip()
    if gst_number:
        # Simple GSTIN validation
        gst_cleaned = gst_number.strip().upper()
        if len(gst_cleaned) != 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GST number must be exactly 15 characters long."
            )
        contractor_profile.gst_number = gst_cleaned
    if pan_number:
        # Simple PAN validation
        pan_cleaned = pan_number.strip().upper()
        if len(pan_cleaned) != 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PAN number must be exactly 10 characters long."
            )
        contractor_profile.pan_number = pan_cleaned
        
    # 2. Update KYC Documents
    if profile_picture:
        ext = os.path.splitext(profile_picture.filename)[1]
        filename = f"contractor_{current_user.id}_logo{ext}"
        path = kyc_dir / filename
        with path.open("wb") as buffer:
            shutil.copyfileobj(profile_picture.file, buffer)
        contractor_profile.profile_picture = f"/uploads/kyc/{filename}"
        
    if business_license:
        ext = os.path.splitext(business_license.filename)[1]
        filename = f"contractor_{current_user.id}_license{ext}"
        path = kyc_dir / filename
        with path.open("wb") as buffer:
            shutil.copyfileobj(business_license.file, buffer)
        contractor_profile.business_license = f"/uploads/kyc/{filename}"
        
    # Queue for review
    contractor_profile.kyc_status = KycStatus.pending
    contractor_profile.rejection_reason = None
    
    db.add(contractor_profile)
    db.commit()
    db.refresh(contractor_profile)
    return contractor_profile
