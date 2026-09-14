from decimal import Decimal
from sqlalchemy import Integer, String, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

class Service(Base):
    __tablename__ = "services"
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    icon_url: Mapped[str] = mapped_column(String(255), nullable=True)
    base_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    bookings = relationship("Booking", back_populates="service")
