from sqlalchemy.orm import relationship
from app.models.base_class import Base
from app.models.payment_status_log import PaymentStatusLog
from app.models.system_config import SystemConfig
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.payment import Payment
from app.models.tax_period import TaxPeriod
from app.models.tax_rate import TaxRate
from app.models.document_type import DocumentType

# Configurar las relaciones
User.vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
User.document_type_rel = relationship("DocumentType", back_populates="users")
User.payment_logs = relationship("PaymentStatusLog", back_populates="user")

Vehicle.owner = relationship("User", back_populates="vehicles")
Vehicle.payments = relationship("Payment", back_populates="vehicle", cascade="all, delete-orphan")

Payment.vehicle = relationship("Vehicle", back_populates="payments")
Payment.tax_period = relationship("TaxPeriod", back_populates="payments")
Payment.status_logs = relationship("PaymentStatusLog", back_populates="payment", cascade="all, delete-orphan")
Payment.correction_payment = relationship("Payment", remote_side=[Payment.id], backref="corrected_by")

DocumentType.users = relationship("User", back_populates="document_type_rel")

TaxPeriod.payments = relationship("Payment", back_populates="tax_period", cascade="all, delete-orphan")
TaxPeriod.tax_rates = relationship("TaxRate", back_populates="tax_period", cascade="all, delete-orphan")

TaxRate.tax_period = relationship("TaxPeriod", back_populates="tax_rates")

PaymentStatusLog.payment = relationship("Payment", back_populates="status_logs")
PaymentStatusLog.user = relationship("User", back_populates="payment_logs")

__all__ = [
    "User", "Vehicle", "Payment", "TaxPeriod", "TaxRate",
    "DocumentType", "PaymentStatusLog", "SystemConfig", "Base"
]
