from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Integer, func, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base
from app.models.user_role import user_roles

class User(Base):
    __tablename__ = "users"
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    language_preference: Mapped[str] = mapped_column(String(20), default="English", server_default="English")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    location_lat: Mapped[Decimal] = mapped_column(DECIMAL(10, 8), nullable=True)
    location_lng: Mapped[Decimal] = mapped_column(DECIMAL(11, 8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    worker_profile = relationship("Worker", back_populates="user", uselist=False, cascade="all, delete-orphan")
    contractor_profile = relationship("Contractor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bookings_as_customer = relationship("Booking", back_populates="customer", foreign_keys="[Booking.customer_id]")
