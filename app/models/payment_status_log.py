from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Enum, Index
from app.models.base_class import Base
from app.models.payment import PaymentProcessStatus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .payment import Payment
    from .user import User


class PaymentStatusLog(Base):
    payment_id: Mapped[int] = mapped_column(ForeignKey("payment.id"), nullable=False)
    status: Mapped[PaymentProcessStatus] = mapped_column(Enum(PaymentProcessStatus), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    details: Mapped[str | None] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    change_reason: Mapped[str | None] = mapped_column(String)

    payment: Mapped["Payment"] = relationship("Payment", back_populates="status_logs")
    user: Mapped["User"] = relationship("User", back_populates="payment_logs")

    __table_args__ = (Index('idx_payment_status_log_timestamp', 'payment_id', 'timestamp'),)
