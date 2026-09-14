import uuid
import enum
from decimal import Decimal
from sqlalchemy import Uuid, Integer, String, DECIMAL, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class KycStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class AvailabilityStatus(str, enum.Enum):
    available_now = "available_now"
    available_today = "available_today"
    unavailable = "unavailable"

class Worker(Base):
    __tablename__ = "workers"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., 'Plumber', 'Electrician'
    experience_years: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pricing_per_hour: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), default=Decimal("0.00"), server_default="0.00")
    total_jobs_done: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus),
        default=AvailabilityStatus.available_now,
        server_default="available_now"
    )
    location_lat: Mapped[Decimal] = mapped_column(DECIMAL(10, 8), nullable=True)
    location_lng: Mapped[Decimal] = mapped_column(DECIMAL(11, 8), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    area_mohalla: Mapped[str] = mapped_column(String(100), nullable=True)
    working_radius_km: Mapped[int] = mapped_column(Integer, nullable=True, default=10)
    additional_skills: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    languages: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    
    # KYC & Profile Fields
    profile_picture: Mapped[str] = mapped_column(String(255), nullable=True)  # Selfie photo path
    aadhaar_number: Mapped[str] = mapped_column(String(12), nullable=True)     # 12-digit Aadhaar number
    aadhaar_image_front: Mapped[str] = mapped_column(String(255), nullable=True) # front photo path
    aadhaar_image_back: Mapped[str] = mapped_column(String(255), nullable=True)  # back photo path
    kyc_status: Mapped[KycStatus] = mapped_column(
        Enum(KycStatus), 
        default=KycStatus.pending, 
        server_default="pending"
    )
    rejection_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="worker_profile")
    bookings_as_worker = relationship("Booking", back_populates="worker")
