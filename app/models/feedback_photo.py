import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Uuid, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class PhotoReviewStatus(str, enum.Enum):
    pending = "PENDING"
    approved = "APPROVED"
    rejected = "REJECTED"

class FeedbackPhoto(Base):
    __tablename__ = "feedback_photos"
    
    feedback_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("feedbacks.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    status: Mapped[str] = mapped_column(
        String(20), 
        default=PhotoReviewStatus.pending.value, 
        server_default="PENDING", 
        index=True, 
        nullable=False
    )
    rejection_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    
    reward_granted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    reward_coins: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    
    reviewed_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    feedback = relationship("Feedback", back_populates="photos")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
