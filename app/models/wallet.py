import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Uuid, Integer, DECIMAL, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class Wallet(Base):
    __tablename__ = "wallets"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), server_default="0.00")
    purchased_coins: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    earned_coins: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    
    @property
    def total_coins(self) -> int:
        return (self.purchased_coins or 0) + (self.earned_coins or 0)

    # Relationships
    user = relationship("User", back_populates="wallet")
    coin_ledger = relationship("CoinLedger", back_populates="wallet", cascade="all, delete-orphan", order_by="desc(CoinLedger.created_at)")
