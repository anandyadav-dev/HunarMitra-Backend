from uuid import UUID
import random
from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreate

class CRUDBooking(CRUDBase[Booking, BookingCreate, dict]):
    def get_by_customer(
        self, db: Session, customer_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        """
        List booking history for a specific customer.
        """
        return (
            db.query(Booking)
            .filter(Booking.customer_id == customer_id)
            .order_by(Booking.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_worker(
        self, db: Session, worker_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        """
        List bookings assigned to a specific worker.
        """
        return (
            db.query(Booking)
            .filter(Booking.worker_id == worker_id)
            .order_by(Booking.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_otp(
        self, db: Session, *, obj_in: BookingCreate, customer_id: UUID
    ) -> Booking:
        """
        Creates a new booking with a random 6-digit OTP verification code.
        """
        # Generate numeric 6-digit OTP code (for completion validation)
        otp = f"{random.randint(100000, 999999)}"
        
        db_obj = Booking(
            customer_id=customer_id,
            worker_id=obj_in.worker_id,
            service_id=obj_in.service_id,
            booking_date=obj_in.booking_date,
            preferred_time=obj_in.preferred_time,
            address=obj_in.address,
            status=BookingStatus.pending,
            otp_verification=otp
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

booking = CRUDBooking(Booking)
