import uuid
from datetime import datetime, timezone
from sqlalchemy import Uuid, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class Engagement(Base):
    __tablename__ = "engagements"
    
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workers.id", ondelete="CASCADE"), index=True, nullable=False)
    engagement_type: Mapped[str] = mapped_column(String(50), default="CONTACT_UNLOCK", server_default="CONTACT_UNLOCK", nullable=False)
    coins_spent: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    purchased_coins_spent: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    earned_coins_spent: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", server_default="ACTIVE", nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    worker = relationship("Worker", foreign_keys=[worker_id])
    feedbacks = relationship("Feedback", back_populates="engagement")
