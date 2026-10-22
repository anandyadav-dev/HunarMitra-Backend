import uuid
from datetime import datetime, timezone
from sqlalchemy import Uuid, Integer, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    engagement_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("engagements.id", ondelete="SET NULL"), nullable=True, index=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workers.id", ondelete="SET NULL"), nullable=True, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5
    category: Mapped[str] = mapped_column(String(50), default="WORKER_EXPERIENCE", server_default="WORKER_EXPERIENCE")
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    reward_granted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    reward_coins: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    worker = relationship("Worker", foreign_keys=[worker_id])
    engagement = relationship("Engagement", back_populates="feedbacks")
    photos = relationship("FeedbackPhoto", back_populates="feedback", cascade="all, delete-orphan")
