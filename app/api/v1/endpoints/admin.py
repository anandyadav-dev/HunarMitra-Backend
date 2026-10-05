from uuid import UUID
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from pydantic import BaseModel, Field

from app.api import deps
from app.models.user import User
from app.models.role import Role
from app.models.worker import Worker, KycStatus
from app.models.contractor import Contractor
from app.models.booking import Booking, BookingStatus
from app.models.wallet import Wallet
from app.models.service import Service
from app.models.work_proof import WorkProof
from app.schemas.service import ServiceCreate, ServiceUpdate

router = APIRouter()
require_admin = deps.RoleChecker(["admin"])

# Verification Request DTOs
class KycVerificationRequest(BaseModel):
    status: str = Field(..., description="Must be 'approved' or 'rejected'")
    rejection_reason: Optional[str] = None

class WalletAdjustmentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount to adjust")
    type: str = Field(..., description="Must be 'credit' or 'debit'")
    description: Optional[str] = None

class BookingStatusUpdateRequest(BaseModel):
    status: BookingStatus = Field(..., description="New status for the booking")


@router.get("/admin/dashboard-stats")
def get_dashboard_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Fetch comprehensive statistical metrics and charts datasets for the Admin Dashboard.
    """
    # 1. KPI Counts
    total_users = db.query(User).count()
    total_workers = db.query(Worker).count()
    total_contractors = db.query(Contractor).count()
    total_bookings = db.query(Booking).count()
    
    # Revenue is the sum of total_amount for COMPLETED bookings
    total_revenue = db.query(func.sum(Booking.total_amount))\
        .filter(Booking.status == BookingStatus.completed)\
        .scalar() or Decimal("0.00")
        
    pending_kyc_workers = db.query(Worker).filter(Worker.kyc_status == KycStatus.pending).count()
    pending_kyc_contractors = db.query(Contractor).filter(Contractor.kyc_status == KycStatus.pending).count()
    pending_kycs_count = pending_kyc_workers + pending_kyc_contractors
    
    active_bookings_count = db.query(Booking).filter(
        Booking.status.in_([BookingStatus.accepted, BookingStatus.in_progress, BookingStatus.pending])
    ).count()

    # 2. Charts: Revenue by Date (last 30 days)
    today = date.today()
    start_date = today - timedelta(days=30)
    
    revenue_query = db.query(
        Booking.booking_date,
        func.sum(Booking.total_amount)
    ).filter(
        and_(
            Booking.status == BookingStatus.completed,
            Booking.booking_date >= start_date
        )
    ).group_by(Booking.booking_date).all()
    
    revenue_map = {r[0]: float(r[1] or 0.0) for r in revenue_query}
    revenue_by_date = []
    
    # Fill in potential blank dates for smooth lines
    for i in range(31):
        d = start_date + timedelta(days=i)
        revenue_by_date.append({
            "date": d.strftime("%Y-%m-%d"),
            "revenue": revenue_map.get(d, 0.0)
        })

    # 3. Charts: Bookings by Status
    status_query = db.query(
        Booking.status,
        func.count(Booking.id)
    ).group_by(Booking.status).all()
    bookings_by_status = {s[0].value: s[1] for s in status_query}
    # Ensure all statuses exist
    for stat in BookingStatus:
        if stat.value not in bookings_by_status:
            bookings_by_status[stat.value] = 0

    # 4. Charts: Service Category Performance
    service_query = db.query(
        Service.name,
        func.count(Booking.id)
    ).join(Booking, Booking.service_id == Service.id)\
     .group_by(Service.name).all()
    category_performance = [{"category": item[0], "count": item[1]} for item in service_query]

    # 5. Recent Activity Feed (dynamic combined query)
    recent_activities = []
    
    # Recent users
    recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
    for u in recent_users:
        recent_activities.append({
            "id": f"user-{u.id}",
            "type": "registration",
            "message": f"New user registration: {u.full_name or 'Unregistered'} ({u.phone_number})",
            "timestamp": u.created_at.isoformat()
        })
        
    # Recent bookings
    recent_bk = db.query(Booking).order_by(desc(Booking.id)).limit(5).all()
    for b in recent_bk:
        status_text = b.status.value
        recent_activities.append({
            "id": f"booking-{b.id}",
            "type": "booking",
            "message": f"Booking #{b.id} is currently {status_text} (Service: {b.service.name})",
            "timestamp": datetime.combine(b.booking_date, datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()
        })
        
    # Recent worker KYC requests
    recent_kyc = db.query(Worker).filter(Worker.kyc_status != KycStatus.approved).order_by(desc(Worker.id)).limit(5).all()
    for wk in recent_kyc:
        name = wk.user.full_name if wk.user else "Worker"
        recent_activities.append({
            "id": f"kyc-{wk.id}",
            "type": "kyc",
            "message": f"Artisan {name} updated status to KYC {wk.kyc_status.value}",
            "timestamp": datetime.now(timezone.utc).isoformat() # Fallback for sorting
        })
        
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activities = recent_activities[:10]

    # 6. Wallet Volume details
    total_balances = db.query(func.sum(Wallet.balance)).scalar() or Decimal("0.00")

    return {
        "total_users": total_users,
        "total_workers": total_workers,
        "total_contractors": total_contractors,
        "total_bookings": total_bookings,
        "total_revenue": float(total_revenue),
        "pending_kycs_count": pending_kycs_count,
        "active_bookings_count": active_bookings_count,
        "total_balances": float(total_balances),
        "revenue_by_date": revenue_by_date,
        "bookings_by_status": bookings_by_status,
        "category_performance": category_performance,
        "recent_activities": recent_activities
    }


# ==================== USER MANAGEMENT ====================

@router.get("/admin/users")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    is_deleted: Optional[bool] = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(User).filter(User.is_deleted == is_deleted)
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
        
    if search:
        query = query.filter(
            or_(
                User.phone_number.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
        
    if role:
        query = query.join(User.roles).filter(func.lower(Role.name) == role.lower())
        
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "phone_number": u.phone_number,
            "full_name": u.full_name,
            "language_preference": u.language_preference,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat(),
            "roles": [r.name for r in u.roles],
            "wallet_balance": float(u.wallet.balance) if u.wallet else 0.0,
            "is_active": u.is_active,
            "is_deleted": u.is_deleted
        })
        
    return {"total": total, "items": result}


@router.get("/admin/users/{id}")
def get_user_details(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
    bookings = db.query(Booking).filter(Booking.customer_id == id).order_by(desc(Booking.id)).all()
    bookings_data = []
    for b in bookings:
        bookings_data.append({
            "id": b.id,
            "service": b.service.name if b.service else "Unknown",
            "booking_date": b.booking_date.strftime("%Y-%m-%d"),
            "preferred_time": b.preferred_time,
            "status": b.status.value,
            "total_amount": float(b.total_amount) if b.total_amount else None
        })
        
    worker_profile = None
    if user_obj.worker_profile:
        wp = user_obj.worker_profile
        worker_profile = {
            "id": wp.id,
            "category": wp.category,
            "experience_years": wp.experience_years,
            "pricing_per_hour": float(wp.pricing_per_hour),
            "bio": wp.bio,
            "rating": float(wp.rating),
            "total_jobs_done": wp.total_jobs_done,
            "kyc_status": wp.kyc_status.value
        }
        
    contractor_profile = None
    if user_obj.contractor_profile:
        cp = user_obj.contractor_profile
        contractor_profile = {
            "id": cp.id,
            "company_name": cp.company_name,
            "gst_number": cp.gst_number,
            "pan_number": cp.pan_number,
            "kyc_status": cp.kyc_status.value
        }

    return {
        "id": user_obj.id,
        "phone_number": user_obj.phone_number,
        "full_name": user_obj.full_name,
        "language_preference": user_obj.language_preference,
        "is_verified": user_obj.is_verified,
        "is_active": user_obj.is_active,
        "is_deleted": user_obj.is_deleted,
        "created_at": user_obj.created_at.isoformat(),
        "roles": [r.name for r in user_obj.roles],
        "wallet": {
            "balance": float(user_obj.wallet.balance) if user_obj.wallet else 0.0,
            "last_updated": user_obj.wallet.last_updated.isoformat() if user_obj.wallet else None
        },
        "worker_profile": worker_profile,
        "contractor_profile": contractor_profile,
        "bookings_history": bookings_data
    }


@router.put("/admin/users/{id}")
def update_user_details(
    id: UUID,
    full_name: Optional[str] = Body(None),
    language_preference: Optional[str] = Body(None),
    is_verified: Optional[bool] = Body(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
    if full_name is not None:
        user_obj.full_name = full_name
    if language_preference is not None:
        user_obj.language_preference = language_preference
    if is_verified is not None:
        user_obj.is_verified = is_verified
        
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return {"message": "User details updated successfully"}


@router.put("/admin/users/{id}/status")
def update_user_status(
    id: UUID,
    is_active: bool = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user_obj.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend yourself.")
    user_obj.is_active = is_active
    db.commit()
    return {"message": "User status updated successfully"}

@router.delete("/admin/users/{id}")
def delete_user(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    # Prevent self deletion
    if user_obj.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete yourself.")
        
    user_obj.is_deleted = True
    if user_obj.worker_profile:
        user_obj.worker_profile.is_deleted = True
    if user_obj.contractor_profile:
        user_obj.contractor_profile.is_deleted = True
    if user_obj.wallet:
        user_obj.wallet.is_deleted = True
        
    db.commit()
    return {"message": "User deleted successfully"}


@router.delete("/admin/users/{id}/permanent")
def delete_user_permanent(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    if user_obj.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot permanently delete yourself.")
        
    db.delete(user_obj)
    db.commit()
    return {"message": "User permanently deleted."}


@router.put("/admin/users/{id}/restore")
def restore_user(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    user_obj.is_deleted = False
    db.commit()
    return {"message": "User restored successfully."}


class AddRoleRequest(BaseModel):
    role_name: str
    description: Optional[str] = None
    parent_role_name: Optional[str] = None

@router.post("/admin/users/{id}/roles")
def add_user_role(
    id: UUID,
    obj_in: AddRoleRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Assign a role to a user. If the role doesn't exist, create it.
    Supports hierarchical roles via parent_role_name.
    """
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
    role_name_clean = obj_in.role_name.strip()
    
    # 1. Find or create the role
    role_obj = db.query(Role).filter(func.lower(Role.name) == role_name_clean.lower()).first()
    if not role_obj:
        # Resolve parent if specified
        parent_id = None
        if obj_in.parent_role_name:
            parent_role = db.query(Role).filter(func.lower(Role.name) == obj_in.parent_role_name.strip().lower()).first()
            if parent_role:
                parent_id = parent_role.id
                
        role_obj = Role(
            name=role_name_clean,
            description=obj_in.description or f"{role_name_clean.capitalize()} Role",
            parent_id=parent_id
        )
        db.add(role_obj)
        db.commit()
        db.refresh(role_obj)
        
    # 2. Assign the role to the user if they don't already have it
    if role_obj not in user_obj.roles:
        user_obj.roles.append(role_obj)
        db.add(user_obj)
        db.commit()
        db.refresh(user_obj)
        
    return {"message": f"Role '{role_name_clean}' assigned successfully."}

@router.delete("/admin/users/{id}/roles/{role_name}")
def remove_user_role(
    id: UUID,
    role_name: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Remove a role from a user.
    """
    user_obj = db.get(User, id)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
    # Find the role among the user's roles
    matching_roles = [r for r in user_obj.roles if r.name.lower() == role_name.strip().lower()]
    if not matching_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User does not have role '{role_name}'.")
        
    # Remove the role
    for r in matching_roles:
        user_obj.roles.remove(r)
        
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    
    return {"message": f"Role '{role_name}' removed successfully."}


class RoleCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class RoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

@router.get("/admin/roles")
def list_all_roles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all roles registered in the database, including parent details.
    """
    roles = db.query(Role).all()
    result = []
    for r in roles:
        result.append({
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "parent_id": r.parent_id,
            "parent_name": r.parent.name if r.parent else None
        })
    return result

@router.post("/admin/roles")
def create_role(
    obj_in: RoleCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new role in the system database.
    """
    existing = db.query(Role).filter(func.lower(Role.name) == obj_in.name.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{obj_in.name}' already exists."
        )
        
    if obj_in.parent_id:
        parent = db.get(Role, obj_in.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent role not found."
            )
            
    role = Role(
        name=obj_in.name.strip(),
        description=obj_in.description,
        parent_id=obj_in.parent_id
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "parent_id": role.parent_id
    }

@router.put("/admin/roles/{role_id}")
def update_role(
    role_id: UUID,
    obj_in: RoleUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update role details in the system.
    """
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
        
    if obj_in.parent_id == role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A role cannot be its own parent."
        )
        
    if obj_in.name is not None:
        name_clean = obj_in.name.strip()
        existing = db.query(Role).filter(
            and_(
                func.lower(Role.name) == name_clean.lower(),
                Role.id != role_id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{name_clean}' already exists."
            )
        role.name = name_clean
        
    if obj_in.description is not None:
        role.description = obj_in.description
        
    if obj_in.parent_id is not None:
        if obj_in.parent_id == 0:
            role.parent_id = None
        else:
            parent = db.get(Role, obj_in.parent_id)
            if not parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent role not found.")
            role.parent_id = obj_in.parent_id
            
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "parent_id": role.parent_id
    }

@router.delete("/admin/roles/{role_id}")
def delete_role(
    role_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a role from the database.
    """
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
        
    if role.name.lower() in ["admin", "customer", "worker", "contractor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Core system role '{role.name}' cannot be deleted."
        )
        
    db.delete(role)
    db.commit()
    return {"message": f"Role '{role.name}' deleted successfully."}


# ==================== WORKER MANAGEMENT ====================

@router.get("/admin/workers")
def list_workers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    kyc_status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_deleted: Optional[bool] = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(Worker).join(User).filter(Worker.is_deleted == is_deleted)
    
    if kyc_status:
        query = query.filter(Worker.kyc_status == kyc_status)
        
    if category:
        query = query.filter(Worker.category == category)
        
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%"),
                Worker.bio.ilike(f"%{search}%")
            )
        )
        
    total = query.count()
    workers = query.order_by(desc(Worker.id)).offset(skip).limit(limit).all()
    
    result = []
    for w in workers:
        result.append({
            "id": w.id,
            "user_id": w.user_id,
            "category": w.category,
            "experience_years": w.experience_years,
            "pricing_per_hour": float(w.pricing_per_hour),
            "rating": float(w.rating),
            "total_jobs_done": w.total_jobs_done,
            "availability_status": w.availability_status,
            "kyc_status": w.kyc_status.value,
            "rejection_reason": w.rejection_reason,
            "is_active": w.is_active,
            "is_deleted": w.is_deleted,
            "user": {
                "id": w.user.id,
                "full_name": w.user.full_name,
                "phone_number": w.user.phone_number,
                "is_verified": w.user.is_verified
            }
        })
        
    return {"total": total, "items": result}


@router.put("/admin/workers/{id}/status")
def update_worker_status(
    id: UUID,
    is_active: bool = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    worker_obj = db.get(Worker, id)
    if not worker_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    worker_obj.is_active = is_active
    db.commit()
    return {"message": "Worker status updated successfully"}

@router.delete("/admin/workers/{id}")
def delete_worker(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    worker_obj = db.get(Worker, id)
    if not worker_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    
    worker_obj.is_deleted = True
    db.commit()
    return {"message": "Worker deleted successfully"}


@router.delete("/admin/workers/{id}/permanent")
def delete_worker_permanent(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    worker_obj = db.get(Worker, id)
    if not worker_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    
    db.delete(worker_obj)
    db.commit()
    return {"message": "Worker permanently deleted."}


@router.put("/admin/workers/{id}/restore")
def restore_worker(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    worker_obj = db.get(Worker, id)
    if not worker_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    
    worker_obj.is_deleted = False
    db.commit()
    return {"message": "Worker restored successfully."}


@router.get("/admin/workers/{id}")
def get_worker_details(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    worker_obj = db.get(Worker, id)
    if not worker_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker profile not found.")
        
    # Get bookings
    bookings = db.query(Booking).filter(Booking.worker_id == id).order_by(desc(Booking.id)).all()
    bookings_data = []
    for b in bookings:
        bookings_data.append({
            "id": b.id,
            "customer_name": b.customer.full_name if b.customer else "Unknown",
            "booking_date": b.booking_date.strftime("%Y-%m-%d"),
            "status": b.status.value,
            "total_amount": float(b.total_amount) if b.total_amount else None
        })

    return {
        "id": worker_obj.id,
        "user_id": worker_obj.user_id,
        "category": worker_obj.category,
        "experience_years": worker_obj.experience_years,
        "pricing_per_hour": float(worker_obj.pricing_per_hour),
        "bio": worker_obj.bio,
        "rating": float(worker_obj.rating),
        "total_jobs_done": worker_obj.total_jobs_done,
        "availability_status": worker_obj.availability_status,
        "location_lat": float(worker_obj.location_lat) if worker_obj.location_lat else None,
        "location_lng": float(worker_obj.location_lng) if worker_obj.location_lng else None,
        "profile_picture": worker_obj.profile_picture,
        "aadhaar_number": worker_obj.aadhaar_number,
        "aadhaar_image_front": worker_obj.aadhaar_image_front,
        "aadhaar_image_back": worker_obj.aadhaar_image_back,
        "kyc_status": worker_obj.kyc_status.value,
        "rejection_reason": worker_obj.rejection_reason,
        "is_active": worker_obj.is_active,
        "is_deleted": worker_obj.is_deleted,
        "user": {
            "id": worker_obj.user.id,
            "full_name": worker_obj.user.full_name,
            "phone_number": worker_obj.user.phone_number,
            "is_verified": worker_obj.user.is_verified,
            "created_at": worker_obj.user.created_at.isoformat()
        },
        "bookings_history": bookings_data
    }


@router.post("/admin/workers/{id}/verify")
def verify_worker(
    id: UUID,
    req: KycVerificationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    worker_obj = db.get(Worker, id)
    if not worker_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker profile not found.")
        
    status_val = req.status.lower()
    if status_val == "approved":
        worker_obj.kyc_status = KycStatus.approved
        worker_obj.rejection_reason = None
        # Verify user as well
        if worker_obj.user:
            worker_obj.user.is_verified = True
    elif status_val == "rejected":
        worker_obj.kyc_status = KycStatus.rejected
        worker_obj.rejection_reason = req.rejection_reason or "Documents do not meet guidelines."
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value. Use 'approved' or 'rejected'.")
        
    db.add(worker_obj)
    db.commit()
    return {"message": f"Worker KYC status set to {status_val}"}


# ==================== CONTRACTOR MANAGEMENT ====================

@router.get("/admin/contractors")
def list_contractors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    kyc_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_deleted: Optional[bool] = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(Contractor).join(User).filter(Contractor.is_deleted == is_deleted)
    
    if kyc_status:
        query = query.filter(Contractor.kyc_status == kyc_status)
        
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%"),
                Contractor.company_name.ilike(f"%{search}%")
            )
        )
        
    total = query.count()
    contractors = query.order_by(desc(Contractor.id)).offset(skip).limit(limit).all()
    
    result = []
    for c in contractors:
        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "company_name": c.company_name,
            "gst_number": c.gst_number,
            "pan_number": c.pan_number,
            "kyc_status": c.kyc_status.value,
            "rejection_reason": c.rejection_reason,
            "is_active": c.is_active,
            "is_deleted": c.is_deleted,
            "user": {
                "id": c.user.id,
                "full_name": c.user.full_name,
                "phone_number": c.user.phone_number,
                "is_verified": c.user.is_verified
            }
        })
        
    return {"total": total, "items": result}


@router.put("/admin/contractors/{id}/status")
def update_contractor_status(
    id: UUID,
    is_active: bool = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    contractor_obj = db.get(Contractor, id)
    if not contractor_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contractor not found.")
    contractor_obj.is_active = is_active
    db.commit()
    return {"message": "Contractor status updated successfully"}

@router.delete("/admin/contractors/{id}")
def delete_contractor(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    contractor_obj = db.get(Contractor, id)
    if not contractor_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contractor not found.")
    
    contractor_obj.is_deleted = True
    db.commit()
    return {"message": "Contractor deleted successfully"}


@router.delete("/admin/contractors/{id}/permanent")
def delete_contractor_permanent(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    contractor_obj = db.get(Contractor, id)
    if not contractor_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contractor not found.")
    
    db.delete(contractor_obj)
    db.commit()
    return {"message": "Contractor permanently deleted."}


@router.put("/admin/contractors/{id}/restore")
def restore_contractor(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    contractor_obj = db.get(Contractor, id)
    if not contractor_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contractor not found.")
    
    contractor_obj.is_deleted = False
    db.commit()
    return {"message": "Contractor restored successfully."}


@router.get("/admin/contractors/{id}")
def get_contractor_details(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    contractor_obj = db.get(Contractor, id)
    if not contractor_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contractor profile not found.")
        
    return {
        "id": contractor_obj.id,
        "user_id": contractor_obj.user_id,
        "company_name": contractor_obj.company_name,
        "gst_number": contractor_obj.gst_number,
        "pan_number": contractor_obj.pan_number,
        "business_license": contractor_obj.business_license,
        "profile_picture": contractor_obj.profile_picture,
        "kyc_status": contractor_obj.kyc_status.value,
        "rejection_reason": contractor_obj.rejection_reason,
        "is_active": contractor_obj.is_active,
        "is_deleted": contractor_obj.is_deleted,
        "user": {
            "id": contractor_obj.user.id,
            "full_name": contractor_obj.user.full_name,
            "phone_number": contractor_obj.user.phone_number,
            "is_verified": contractor_obj.user.is_verified,
            "created_at": contractor_obj.user.created_at.isoformat()
        }
    }


@router.post("/admin/contractors/{id}/verify")
def verify_contractor(
    id: UUID,
    req: KycVerificationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    contractor_obj = db.get(Contractor, id)
    if not contractor_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contractor profile not found.")
        
    status_val = req.status.lower()
    if status_val == "approved":
        contractor_obj.kyc_status = KycStatus.approved
        contractor_obj.rejection_reason = None
        if contractor_obj.user:
            contractor_obj.user.is_verified = True
    elif status_val == "rejected":
        contractor_obj.kyc_status = KycStatus.rejected
        contractor_obj.rejection_reason = req.rejection_reason or "GST / License document invalid."
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value. Use 'approved' or 'rejected'.")
        
    db.add(contractor_obj)
    db.commit()
    return {"message": f"Contractor KYC status set to {status_val}"}


# ==================== BOOKINGS MANAGEMENT ====================

@router.get("/admin/bookings")
def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(Booking).join(Service)
    
    if status:
        query = query.filter(Booking.status == status)
        
    if search:
        query = query.filter(
            or_(
                Booking.address.ilike(f"%{search}%"),
                Booking.otp_verification.ilike(f"%{search}%")
            )
        )
        
    total = query.count()
    bookings = query.order_by(desc(Booking.id)).offset(skip).limit(limit).all()
    
    result = []
    for b in bookings:
        result.append({
            "id": b.id,
            "customer_id": b.customer_id,
            "worker_id": b.worker_id,
            "service_id": b.service_id,
            "booking_date": b.booking_date.strftime("%Y-%m-%d"),
            "preferred_time": b.preferred_time,
            "address": b.address,
            "status": b.status.value,
            "total_amount": float(b.total_amount) if b.total_amount else None,
            "otp_verification": b.otp_verification,
            "service": {
                "id": b.service.id,
                "name": b.service.name
            },
            "customer": {
                "id": b.customer.id,
                "full_name": b.customer.full_name,
                "phone_number": b.customer.phone_number
            } if b.customer else None,
            "worker": {
                "id": b.worker.id,
                "category": b.worker.category,
                "full_name": b.worker.user.full_name if b.worker.user else "Unknown"
            } if b.worker else None
        })
        
    return {"total": total, "items": result}


@router.get("/admin/bookings/{id}")
def get_booking_details(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    booking_obj = db.get(Booking, id)
    if not booking_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
        
    work_proofs = []
    for wp in booking_obj.work_proofs:
        work_proofs.append({
            "id": wp.id,
            "image_url": wp.image_url,
            "uploaded_at": wp.uploaded_at.isoformat()
        })
        
    return {
        "id": booking_obj.id,
        "customer_id": booking_obj.customer_id,
        "worker_id": booking_obj.worker_id,
        "service_id": booking_obj.service_id,
        "booking_date": booking_obj.booking_date.strftime("%Y-%m-%d"),
        "preferred_time": booking_obj.preferred_time,
        "address": booking_obj.address,
        "status": booking_obj.status.value,
        "total_amount": float(booking_obj.total_amount) if booking_obj.total_amount else None,
        "otp_verification": booking_obj.otp_verification,
        "service": {
            "id": booking_obj.service.id,
            "name": booking_obj.service.name,
            "base_price": float(booking_obj.service.base_price)
        },
        "customer": {
            "id": booking_obj.customer.id,
            "full_name": booking_obj.customer.full_name,
            "phone_number": booking_obj.customer.phone_number
        } if booking_obj.customer else None,
        "worker": {
            "id": booking_obj.worker.id,
            "category": booking_obj.worker.category,
            "pricing_per_hour": float(booking_obj.worker.pricing_per_hour),
            "experience_years": booking_obj.worker.experience_years,
            "full_name": booking_obj.worker.user.full_name if booking_obj.worker.user else "Unknown",
            "phone_number": booking_obj.worker.user.phone_number if booking_obj.worker.user else "Unknown"
        } if booking_obj.worker else None,
        "work_proofs": work_proofs
    }


@router.put("/admin/bookings/{id}/status")
def update_booking_status(
    id: UUID,
    req: BookingStatusUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    booking_obj = db.get(Booking, id)
    if not booking_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
        
    old_status = booking_obj.status
    new_status = req.status
    booking_obj.status = new_status
    
    # If state changes to completed, check wallet transfer
    if new_status == BookingStatus.completed and old_status != BookingStatus.completed:
        total_amount = booking_obj.total_amount or booking_obj.service.base_price or Decimal("150.00")
        booking_obj.total_amount = total_amount
        
        customer_wallet = db.query(Wallet).filter(Wallet.user_id == booking_obj.customer_id).first()
        worker_profile = booking_obj.worker
        if worker_profile:
            worker_wallet = db.query(Wallet).filter(Wallet.user_id == worker_profile.user_id).first()
            if customer_wallet and worker_wallet:
                customer_wallet.balance -= total_amount
                worker_wallet.balance += total_amount
                db.add(customer_wallet)
                db.add(worker_wallet)
                
            worker_profile.total_jobs_done += 1
            db.add(worker_profile)
            
    db.add(booking_obj)
    db.commit()
    return {"message": f"Booking status updated from {old_status.value} to {new_status.value}"}


# ==================== SERVICES MANAGEMENT ====================

@router.get("/admin/services")
def list_services(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    services = db.query(Service).all()
    result = []
    for s in services:
        result.append({
            "id": s.id,
            "name": s.name,
            "icon_url": s.icon_url,
            "base_price": float(s.base_price)
        })
    return result


@router.post("/admin/services")
def create_service(
    obj_in: ServiceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    existing = db.query(Service).filter(func.lower(Service.name) == obj_in.name.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this name already exists.")
        
    db_obj = Service(
        name=obj_in.name,
        icon_url=obj_in.icon_url,
        base_price=obj_in.base_price
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return {
        "id": db_obj.id,
        "name": db_obj.name,
        "icon_url": db_obj.icon_url,
        "base_price": float(db_obj.base_price)
    }


@router.put("/admin/services/{id}")
def update_service(
    id: UUID,
    obj_in: ServiceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    service_obj = db.get(Service, id)
    if not service_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
        
    if obj_in.name is not None:
        existing = db.query(Service).filter(
            and_(
                func.lower(Service.name) == obj_in.name.lower(),
                Service.id != id
            )
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this name already exists.")
        service_obj.name = obj_in.name
        
    if obj_in.icon_url is not None:
        service_obj.icon_url = obj_in.icon_url
        
    if obj_in.base_price is not None:
        service_obj.base_price = obj_in.base_price
        
    db.add(service_obj)
    db.commit()
    db.refresh(service_obj)
    return {
        "id": service_obj.id,
        "name": service_obj.name,
        "icon_url": service_obj.icon_url,
        "base_price": float(service_obj.base_price)
    }


@router.delete("/admin/services/{id}")
def delete_service(
    id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    service_obj = db.get(Service, id)
    if not service_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
        
    try:
        db.delete(service_obj)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete this service because it is currently linked to booking logs."
        )
    return {"message": "Service deleted successfully"}


# ==================== WALLET & FINANCE ====================

@router.get("/admin/wallets")
def list_wallets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    search: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(Wallet).join(User)
    
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%")
            )
        )
        
    total = query.count()
    wallets = query.order_by(desc(Wallet.balance)).offset(skip).limit(limit).all()
    
    result = []
    for w in wallets:
        result.append({
            "id": w.id,
            "user_id": w.user_id,
            "balance": float(w.balance),
            "last_updated": w.last_updated.isoformat(),
            "user": {
                "id": w.user.id,
                "full_name": w.user.full_name,
                "phone_number": w.user.phone_number,
                "roles": [r.name for r in w.user.roles]
            }
        })
        
    return {"total": total, "items": result}


@router.post("/admin/wallets/{id}/adjust")
def adjust_wallet_balance(
    id: UUID,
    req: WalletAdjustmentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin)
):
    wallet_obj = db.get(Wallet, id)
    if not wallet_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found.")
        
    adj_type = req.type.lower()
    amount = req.amount
    
    if adj_type == "credit":
        wallet_obj.balance += amount
    elif adj_type == "debit":
        if wallet_obj.balance < amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance for debit adjustment.")
        wallet_obj.balance -= amount
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid adjustment type. Use 'credit' or 'debit'.")
        
    db.add(wallet_obj)
    db.commit()
    db.refresh(wallet_obj)
    return {
        "message": f"Successfully {adj_type}ed balance with {float(amount)}",
        "new_balance": float(wallet_obj.balance)
    }
