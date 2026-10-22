import uuid
from datetime import datetime, timezone
from sqlalchemy import Uuid, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class Reward(Base):
    __tablename__ = "rewards"
    
    reward_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    coins_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    max_claims_per_user: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    
    claims = relationship("UserReward", back_populates="reward", cascade="all, delete-orphan")

class UserReward(Base):
    __tablename__ = "user_rewards"
    
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    reward_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rewards.id", ondelete="CASCADE"), nullable=True, index=True)
    reward_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    coins_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reward = relationship("Reward", back_populates="claims")
