import uuid
from sqlalchemy import Uuid, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base
from app.models.user_role import user_roles

class Role(Base):
    __tablename__ = "roles"
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    
    # Self-referential hierarchical relationship
    parent = relationship("Role", remote_side="Role.id", back_populates="sub_roles")
    sub_roles = relationship("Role", back_populates="parent")
    
    # Many-to-many relationship with Users
    users = relationship("User", secondary=user_roles, back_populates="roles")
