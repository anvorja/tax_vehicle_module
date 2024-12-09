from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, Boolean, String, Index, UniqueConstraint
from app.models.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .payment import Payment
    from .tax_rate import TaxRate


class TaxPeriod(Base):
    year: Mapped[int] = mapped_column(nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    due_date: Mapped[date] = mapped_column(nullable=False)
    traffic_light_fee: Mapped[float] = mapped_column(Float, nullable=False)
    min_penalty_uvt: Mapped[int] = mapped_column(nullable=False)
    uvt_value: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    extension_date: Mapped[date | None] = mapped_column()
    observations: Mapped[str | None] = mapped_column(String)

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="tax_period",
        cascade="all, delete-orphan"
    )
    tax_rates: Mapped[list["TaxRate"]] = relationship(
        "TaxRate",
        back_populates="tax_period",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('year', name='uq_tax_period_year'),
        Index('idx_tax_period_dates', 'start_date', 'end_date', 'is_active'),
    )
