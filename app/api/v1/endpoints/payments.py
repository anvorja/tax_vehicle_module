from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.payment_service import PaymentService
from app.services.vehicle_service import VehicleService
from app.schemas.payment_schema import (
    PaymentResponse,
    PSEPaymentRequest,
    PSERedirectResponse,
)

router = APIRouter()


@router.post("/initiate/{plate}", response_model=PaymentResponse)
def initiate_payment(
        plate: str,
        db: Session = Depends(get_db)
):
    """Inicia el proceso de pago para un vehículo"""
    details, error = VehicleService.get_vehicle_tax_details(db, plate)
    if error:
        raise HTTPException(status_code=404, detail=error)

    try:
        # Calcular monto total
        total_amount = details["tax_details"]["base_tax"] + details["tax_details"]["traffic_light_fee"]

        payment_info = PaymentService.initiate_pse_payment(
            db=db,
            vehicle_id=details["vehicle_details"]["id"],
            amount=total_amount,
            bank_code="DEFAULT",  # Este código se actualizará en process-pse
            email="pending"  # Este email se actualizará en process-pse
        )
        return payment_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process-pse/{payment_id}", response_model=PSERedirectResponse)
def process_pse_payment(
        payment_id: int,
        pse_request: PSEPaymentRequest,
        db: Session = Depends(get_db)
):
    """Procesa el pago a través de PSE"""
    try:
        pse_info = PaymentService.process_pse_payment(
            db=db,
            payment_id=payment_id,
            bank_code=pse_request.bank_code
        )
        return pse_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/pse-callback/{transaction_id}", response_model=PaymentResponse)
def pse_callback(
        transaction_id: str,
        status: str = "SUCCESS",
        db: Session = Depends(get_db)
):
    """Callback para actualizar el estado del pago después de PSE"""
    try:
        payment = PaymentService.complete_payment(db, transaction_id, status)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
