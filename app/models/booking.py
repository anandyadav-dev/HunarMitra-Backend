import uuid
from datetime import date
from decimal import Decimal
import enum
from sqlalchemy import Uuid, Integer, String, Date, Text, DECIMAL, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class BookingStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class Booking(Base):
    __tablename__ = "bookings"
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    preferred_time: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), 
        default=BookingStatus.pending, 
        server_default="pending"
    )
    address: Mapped[str] = mapped_column(Text, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True)
    otp_verification: Mapped[str] = mapped_column(String(6), nullable=True)
    
    # Relationships
    customer = relationship("User", back_populates="bookings_as_customer", foreign_keys=[customer_id])
    worker = relationship("Worker", back_populates="bookings_as_worker", foreign_keys=[worker_id])
    service = relationship("Service", back_populates="bookings")
    work_proofs = relationship("WorkProof", back_populates="booking", cascade="all, delete-orphan")
