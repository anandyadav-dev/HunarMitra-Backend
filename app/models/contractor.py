import uuid
from sqlalchemy import Uuid, Integer, String, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base
from app.models.worker import KycStatus

class Contractor(Base):
    __tablename__ = "contractors"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(100), nullable=True)
    gst_number: Mapped[str] = mapped_column(String(15), nullable=True)
    pan_number: Mapped[str] = mapped_column(String(10), nullable=True)
    business_license: Mapped[str] = mapped_column(String(255), nullable=True)  # Business registration/License image
    profile_picture: Mapped[str] = mapped_column(String(255), nullable=True)   # Profile/Company logo
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    work_types: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    kyc_status: Mapped[KycStatus] = mapped_column(
        Enum(KycStatus), 
        default=KycStatus.pending, 
        server_default="pending"
    )
    rejection_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="contractor_profile")
