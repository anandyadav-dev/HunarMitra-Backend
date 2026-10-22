import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Uuid, Integer, String, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class CoinType(str, enum.Enum):
    purchased = "purchased"
    earned = "earned"

class CoinAction(str, enum.Enum):
    credit = "CREDIT"
    debit = "DEBIT"

class CoinLedger(Base):
    __tablename__ = "coin_ledgers"
    
    wallet_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("wallets.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # "CREDIT", "DEBIT"
    coin_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "purchased", "earned"
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Examples: "PURCHASE", "BONUS", "ENGAGEMENT_UNLOCK", "CALL_UNLOCK", "FEEDBACK_REWARD", "SIGNUP_BONUS", "ADMIN_ADJUSTMENT", "REFUND"
    
    balance_purchased_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    balance_earned_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    balance_total_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    
    reference_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    wallet = relationship("Wallet", back_populates="coin_ledger")
    user = relationship("User", foreign_keys=[user_id])
