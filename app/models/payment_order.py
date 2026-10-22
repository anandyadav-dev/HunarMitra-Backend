import uuid
from datetime import datetime, timezone
from decimal import Decimal
import enum
from sqlalchemy import Uuid, Integer, String, DECIMAL, Boolean, DateTime, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class PaymentOrderStatus(str, enum.Enum):
    pending = "PENDING"
    success = "SUCCESS"
    failed = "FAILED"
    cancelled = "CANCELLED"
    expired = "EXPIRED"

class PaymentOrder(Base):
    __tablename__ = "payment_orders"
    
    order_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    pack_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("coin_packs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Preserved pack details at time of order creation (never trust client values; preserved for auditing)
    pack_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pack_code: Mapped[str] = mapped_column(String(50), nullable=False)
    coins: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_coins: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_inr: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", server_default="INR", nullable=False)
    
    status: Mapped[str] = mapped_column(
        String(30), 
        default=PaymentOrderStatus.pending.value, 
        server_default="PENDING", 
        index=True, 
        nullable=False
    )
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)
    gateway_order_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    gateway_payment_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    gateway_signature: Mapped[str] = mapped_column(String(255), nullable=True)
    
    coins_credited: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    credited_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    pack = relationship("CoinPack", foreign_keys=[pack_id])
