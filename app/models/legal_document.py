import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime
from app.models.base_class import Base

class LegalDocument(Base):
    """
    Model for managing platform legal pages (Privacy Policy, Terms and Conditions, etc.).
    slug: 'privacy-policy', 'terms-and-conditions', etc.
    """
    __tablename__ = "legal_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text(length=4294967295), nullable=False)  # LONGTEXT in MySQL
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )
