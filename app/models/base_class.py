import uuid
from typing import Any
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from sqlalchemy import Uuid

class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    
    # Automatically generate table name from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = cls.__name__
        # Convert camelCase/PascalCase to snake_case
        parts = []
        start = 0
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                parts.append(name[start:i].lower())
                start = i
        parts.append(name[start:].lower())
        
        # Pluralize last word simply
        base_name = "_".join(parts)
        if base_name.endswith("y"):
            return base_name[:-1] + "ies"
        elif base_name.endswith("s"):
            return base_name
        else:
            return base_name + "s"
