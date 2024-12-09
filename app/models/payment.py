import enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, ForeignKey, String, Enum, Boolean, Index, UniqueConstraint
from app.models.base_class import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .vehicle import Vehicle
    from .tax_period import TaxPeriod
    from .payment_status_log import PaymentStatusLog


class PaymentProcessStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING_PSE = "pending_pse"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Payment(Base):
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicle.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    due_date: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_method: Mapped[str | None] = mapped_column(String)
    transaction_id: Mapped[str | None] = mapped_column(String, unique=True)
    tax_year: Mapped[int] = mapped_column(nullable=False)
    late_fee: Mapped[float] = mapped_column(Float, default=0.0)
    has_traffic_lights_fee: Mapped[bool] = mapped_column(Boolean, default=True)
    penalties: Mapped[float] = mapped_column(Float, default=0.0)
    tax_period_id: Mapped[int] = mapped_column(ForeignKey("taxperiod.id"))
    invoice_number: Mapped[str | None] = mapped_column(String, unique=True)
    correction_of_payment_id: Mapped[int | None] = mapped_column(ForeignKey("payment.id"))
    bank: Mapped[str | None] = mapped_column(String)
    process_status: Mapped[PaymentProcessStatus] = mapped_column(
        Enum(PaymentProcessStatus),
        nullable=False,
        default=PaymentProcessStatus.INITIATED
    )
    process_message: Mapped[str | None] = mapped_column(String)
    bank_reference: Mapped[str | None] = mapped_column(String)
    paid_at: Mapped[datetime | None] = mapped_column()
    late_payment_fee: Mapped[float] = mapped_column(Float, default=0.0)
    correction_fee: Mapped[float] = mapped_column(Float, default=0.0)
    pse_transaction_id: Mapped[str | None] = mapped_column(String)
    email_notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="payments")
    tax_period: Mapped["TaxPeriod"] = relationship("TaxPeriod", back_populates="payments")
    status_logs: Mapped[list["PaymentStatusLog"]] = relationship(
        "PaymentStatusLog",
        back_populates="payment",
        cascade="all, delete-orphan"
    )

    correction_payment: Mapped[Optional["Payment"]] = relationship(
        "Payment",
        primaryjoin="Payment.correction_of_payment_id==Payment.id",
        remote_side="Payment.id",
        backref="corrected_by"
    )

    __table_args__ = (
        Index('idx_payment_status_date', 'status', 'payment_date'),
        Index('idx_payment_vehicle_year', 'vehicle_id', 'tax_year'),
        UniqueConstraint('vehicle_id', 'tax_period_id', name='uq_vehicle_tax_period'),
    )
