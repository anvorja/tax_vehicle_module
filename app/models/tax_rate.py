from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, Boolean, Enum, ForeignKey, Index
from app.models.base_class import Base
from app.models.vehicle import VehicleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tax_period import TaxPeriod


class TaxRate(Base):
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    min_value: Mapped[float | None] = mapped_column(Float)
    max_value: Mapped[float | None] = mapped_column(Float)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_period_id: Mapped[int] = mapped_column(ForeignKey("taxperiod.id"))
    additional_rate: Mapped[float] = mapped_column(Float, default=0.0)

    tax_period: Mapped["TaxPeriod"] = relationship("TaxPeriod", back_populates="tax_rates")

    __table_args__ = (
        Index('idx_tax_rate_vehicle_type_year', 'vehicle_type', 'year', 'is_active'),
    )
