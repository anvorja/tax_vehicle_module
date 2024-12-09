# document_type.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Index
from app.models.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class DocumentType(Base):
    __tablename__ = "document_type"

    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="document_type_rel")

    __table_args__ = (
        Index('idx_document_type_code_active', 'code', 'is_active'),
    )
