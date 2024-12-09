# app/models/__init__.py
from .document_type import DocumentType
from .payment import Payment
from .payment_status_log import PaymentStatusLog
from .system_config import SystemConfig
from .tax_period import TaxPeriod
from .tax_rate import TaxRate
from .user import User
from .vehicle import Vehicle, VehicleType

__all__ = [
    "DocumentType",
    "Payment",
    "PaymentStatusLog",
    "SystemConfig",
    "TaxPeriod",
    "TaxRate",
    "User",
    "Vehicle",
    "VehicleType",
]