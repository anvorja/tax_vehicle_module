# user.py
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Index
from app.models.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vehicle import Vehicle
    from .document_type import DocumentType
    from .payment_status_log import PaymentStatusLog


class User(Base):
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    document_type_id: Mapped[int] = mapped_column(ForeignKey('document_type.id'), nullable=False)
    document_number: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    notification_email: Mapped[str | None] = mapped_column(String)
    last_login: Mapped[datetime | None] = mapped_column(DateTime)
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    password_reset_token: Mapped[str | None] = mapped_column(String)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    document_type_rel: Mapped["DocumentType"] = relationship("DocumentType", back_populates="users")
    payment_logs: Mapped[list["PaymentStatusLog"]] = relationship("PaymentStatusLog", back_populates="user")

    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_document', 'document_type_id', 'document_number'),
    )
