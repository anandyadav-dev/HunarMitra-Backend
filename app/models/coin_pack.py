from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Integer, String, DECIMAL, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_class import Base

class CoinPack(Base):
    __tablename__ = "coin_packs"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    coins: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_coins: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    price_inr: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    badge_text: Mapped[str] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
