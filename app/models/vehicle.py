import enum
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Float, ForeignKey, Enum, Index
from app.models.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .payment import Payment


class VehicleType(str, enum.Enum):
    PARTICULAR = "particular"
    PUBLIC = "public"
    MOTORCYCLE = "motorcycle"


class TaxStatus(str, enum.Enum):
    UP_TO_DATE = "up_to_date"
    PENDING = "pending"
    OVERDUE = "overdue"
    EXEMPT = "exempt"


class Vehicle(Base):
    plate: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    commercial_value: Mapped[float] = mapped_column(Float, nullable=False)
    is_electric: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    registration_date: Mapped[date] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    engine_displacement: Mapped[float | None] = mapped_column(Float)
    tax_rate: Mapped[float | None] = mapped_column(Float)
    tax_year: Mapped[int | None] = mapped_column()
    discount_type: Mapped[str | None] = mapped_column(String)
    discount_expiry: Mapped[date | None] = mapped_column()
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
    import_declaration: Mapped[str | None] = mapped_column(String)
    last_payment_date: Mapped[datetime | None] = mapped_column()
    next_payment_due: Mapped[datetime | None] = mapped_column()
    has_pending_payments: Mapped[bool] = mapped_column(Boolean, default=False)
    current_tax_status: Mapped[TaxStatus] = mapped_column(Enum(TaxStatus), nullable=False, default=TaxStatus.PENDING)
    current_appraisal: Mapped[float] = mapped_column(Float, nullable=False)
    appraisal_year: Mapped[int] = mapped_column(nullable=False)
    line: Mapped[str | None] = mapped_column(String)
    previous_appraisal: Mapped[float | None] = mapped_column(Float)
    last_tax_calculation: Mapped[datetime | None] = mapped_column()
    requires_traffic_light_fee: Mapped[bool] = mapped_column(Boolean, default=True)

    owner: Mapped["User"] = relationship("User", back_populates="vehicles")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="vehicle", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_vehicle_plate_status', 'plate', 'current_tax_status'),
        Index('idx_vehicle_type_city', 'vehicle_type', 'city'),
    )
