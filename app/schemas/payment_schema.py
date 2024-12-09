from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.payment import PaymentStatus, PaymentProcessStatus


# Schemas existentes
class PaymentBase(BaseModel):
    vehicle_id: int
    amount: float
    tax_year: int
    has_traffic_lights_fee: bool = True


class PaymentCreate(PaymentBase):
    pass


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
    process_message: Optional[str] = None


# Schemas para PSE mejorados
class PSEPaymentRequest(BaseModel):
    plate: str
    document_type: str
    document_number: str
    bank_code: str = Field(..., description="Código del banco seleccionado")
    email: str


class PSERedirectResponse(BaseModel):
    message: Optional[str] = None
    transaction_id: str
    amount: float
    status: str
    reference_number: str
    bank_redirect_url: Optional[str] = None
    payment_date: Optional[str] = None


class PSEBankResponse(BaseModel):
    bank_code: str
    bank_name: str
    status: str


# Schemas de respuesta que existen
class PaymentResponse(PaymentBase):
    id: int
    invoice_number: str
    status: PaymentStatus
    process_status: PaymentProcessStatus
    payment_date: datetime
    due_date: datetime
    payment_method: Optional[str]
    transaction_id: Optional[str]
    late_fee: float = 0.0
    penalties: float = 0.0
    bank: Optional[str]
    process_message: Optional[str]
    bank_reference: Optional[str]
    paid_at: Optional[datetime]
    pse_transaction_id: Optional[str]
    email_notification_sent: bool

    class Config:
        from_attributes = True


class PaymentHistoryResponse(BaseModel):
    payments: list[PaymentResponse]
    total_payments: int
    total_amount_paid: float

    class Config:
        from_attributes = True


class PaymentCompletionResponse(BaseModel):
    transaction_id: str
    status: str
    payment_date: str
    amount: float
    reference_number: str


class PaymentStatusResponse(BaseModel):
    transaction_id: str
    status: str
    amount: float
    reference_number: str
    payment_date: Optional[str] = None
    message: str

    class Config:
        from_attributes = True


class VehiclePaymentHistoryResponse(BaseModel):
    vehicle_info: dict = {
        "periodo_certificacion": "",
        "fecha_consulta": "",
        "placa": "",
        "marca": ""
    }
    ultimo_pago: dict = {
        "periodo_pagado": "",
        "fecha_pago": "",
        "valor_pagado": 0.0
    }
    historial_pagos: List[dict] = [{
        "año": 0,
        "concepto": "",
        "valor": 0.0,
        "estado": ""
    }]

    class Config:
        from_attributes = True
