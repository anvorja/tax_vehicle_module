from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, constr
from pydantic.v1 import Field
from typing_extensions import Annotated


class VehicleBase(BaseModel):
    plate: Annotated[str, Field(pattern="^[A-Z0-9]{6}$")]   # Validación para placas: 3 números y 3 letras
    brand: str
    model: str
    year: int
    vehicle_type: str
    commercial_value: float
    is_electric: bool
    is_hybrid: bool
    city: str
    engine_displacement: Optional[float] = None
    is_new: bool = False
    registration_date: Optional[date] = None


class VehicleCreate(VehicleBase):
    owner_id: int


class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    current_tax_status: str
    has_pending_payments: bool

    class Config:
        from_attributes = True


class VehicleTaxResponse(BaseModel):
    vehicle_id: int
    plate: str
    owner_name: str
    base_tax: float
    traffic_light_fee: float
    late_payment_fee: Optional[float] = 0.0
    penalties: Optional[float] = 0.0
    total_amount: float
    tax_status: str
    due_date: Optional[date]
    last_payment_date: Optional[datetime]

    class Config:
        from_attributes = True


class AccountStatementResponse(BaseModel):
    header: dict
    vehicle_details: dict
    tax_details: dict
    payment_history: list = []

    class Config:
        from_attributes = True


class EmailRequestSchema(BaseModel):
    email: str
    plate: str
    document_type: str
    document_number: str


class ProcessDetailResponse(BaseModel):
    vehicle_info: dict
    pending_payments: list[dict]
    payment_history: list[dict]

    class Config:
        from_attributes = True


class VehicleConsultResponse(BaseModel):
    vehicle_details: dict
    tax_details: dict
    discounts: dict | None

    class Config:
        from_attributes = True

