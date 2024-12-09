from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import re
from app.api.deps import get_db, get_current_user
from app.models import Payment, TaxRate, TaxPeriod
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleType, TaxStatus
from app.schemas.vehicle_schema import VehicleCreate, VehicleResponse, VehicleTaxResponse, ProcessDetailResponse, \
    EmailRequestSchema, AccountStatementResponse
from app.services.payment_service import PaymentService
from app.services.vehicle_service import VehicleService
from app.schemas.vehicle_schema import VehicleConsultResponse
from app.schemas.payment_schema import (
    PSEPaymentRequest,
    PSERedirectResponse,
    PSEBankResponse,
    PaymentCompletionResponse
)

router = APIRouter()


@router.get("/consult", response_model=VehicleConsultResponse)
def consult_vehicle_tax(
        plate: str = Query(..., min_length=6, max_length=6, regex="^[A-Z0-9]{6}$"),
        document_type: str = Query(...),
        document_number: str = Query(...),
        db: Session = Depends(get_db)
):
    """Consulta los detalles de impuesto de un vehículo"""
    details, error = VehicleService.get_vehicle_tax_details(
        db, plate, document_type, document_number
    )
    if error:
        raise HTTPException(status_code=404, detail=error)
    return details


@router.post("/", response_model=VehicleResponse)
def create_vehicle(
        vehicle: VehicleCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Crea un nuevo registro de vehículo"""
    # Validar formato de placa (3 números y 3 letras)
    if not re.match(r'^[A-Z0-9]{6}$', vehicle.plate):
        raise HTTPException(
            status_code=400,
            detail="Formato de placa inválido. Debe contener 6 caracteres alfanuméricos"
        )

    # Verificar si la placa ya existe
    existing_vehicle = db.query(Vehicle).filter(Vehicle.plate == vehicle.plate).first()
    if existing_vehicle:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un vehículo registrado con esta placa"
        )

    # Crear instancia del modelo Vehicle
    db_vehicle = Vehicle(
        plate=vehicle.plate.upper(),
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year,
        vehicle_type=vehicle.vehicle_type,
        commercial_value=vehicle.commercial_value,
        is_electric=vehicle.is_electric,
        is_hybrid=vehicle.is_hybrid,
        city=vehicle.city,
        engine_displacement=vehicle.engine_displacement,
        owner_id=vehicle.owner_id,
        registration_date=vehicle.registration_date or date.today(),
        is_new=vehicle.is_new
    )

    # Validar los datos del vehículo
    is_valid, errors = VehicleService.validate_vehicle_data(db_vehicle)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": errors}
        )

    # Establecer campos calculados
    if db_vehicle.is_new:
        db_vehicle.last_tax_calculation = None
        db_vehicle.next_payment_due = None
        db_vehicle.has_pending_payments = True
    else:
        # Para vehículos existentes, establecer estado inicial
        db_vehicle.current_tax_status = TaxStatus.PENDING
        db_vehicle.has_pending_payments = True

    # Determinar si requiere tarifa de semaforización
    db_vehicle.requires_traffic_light_fee = True
    if vehicle.vehicle_type == VehicleType.MOTORCYCLE and vehicle.engine_displacement <= 125:
        db_vehicle.requires_traffic_light_fee = False

    # Establecer tipos de descuento para vehículos eléctricos/híbridos
    if db_vehicle.is_electric:
        if vehicle.vehicle_type == VehicleType.PUBLIC:
            db_vehicle.discount_type = "ELECTRIC_PUBLIC"
            db_vehicle.discount_expiry = date.today() + timedelta(days=365 * 5)  # 5 años
        else:
            db_vehicle.discount_type = "ELECTRIC_PRIVATE"
            db_vehicle.discount_expiry = date.today() + timedelta(days=365 * 5)
    elif db_vehicle.is_hybrid:
        db_vehicle.discount_type = "HYBRID"
        db_vehicle.discount_expiry = date.today() + timedelta(days=365 * 5)

    try:
        db.add(db_vehicle)
        db.commit()
        db.refresh(db_vehicle)
        return db_vehicle
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al crear el registro del vehículo"
        )


@router.get("/tax-calculation/{plate}", response_model=VehicleTaxResponse)
def calculate_vehicle_tax(
        plate: str,
        db: Session = Depends(get_db)
):
    """Calcula el impuesto para un vehículo específico"""
    vehicle = db.query(Vehicle).filter(Vehicle.plate == plate).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")

    tax_period = db.query(TaxPeriod).filter(TaxPeriod.is_active == True).first()
    if not tax_period:
        raise HTTPException(status_code=404, detail="No hay período fiscal activo")

    tax_rates = db.query(TaxRate).filter(TaxRate.tax_period_id == tax_period.id).all()

    tax_calculation = VehicleService.calculate_total_tax_amount(vehicle, tax_period, tax_rates)

    # Obtener el owner
    owner = db.query(User).filter(User.id == vehicle.owner_id).first()

    # Construir la respuesta completa
    response = VehicleTaxResponse(
        vehicle_id=vehicle.id,
        plate=vehicle.plate,
        owner_name=owner.full_name,
        base_tax=tax_calculation["base_tax"],
        traffic_light_fee=tax_calculation["traffic_light_fee"],
        total_amount=tax_calculation["total_amount"],
        tax_status=vehicle.current_tax_status.value,
        due_date=tax_period.due_date,
        last_payment_date=None  # O puedes obtenerlo de la tabla de pagos si es necesario
    )

    return response


@router.get("/admin/dashboard", response_model=List[VehicleTaxResponse])
def get_tax_dashboard(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Dashboard para administradores con información de impuestos"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    # Obtener el período fiscal activo
    active_tax_period = db.query(TaxPeriod).filter(TaxPeriod.is_active == True).first()
    if not active_tax_period:
        raise HTTPException(status_code=404, detail="No hay período fiscal activo")

    # Obtener tasas de impuesto vigentes
    tax_rates = db.query(TaxRate).filter(TaxRate.tax_period_id == active_tax_period.id).all()

    # Obtener todos los vehículos con sus propietarios
    vehicles = (
        db.query(Vehicle, User)
        .join(User, Vehicle.owner_id == User.id)
        .all()
    )

    dashboard_data = []
    for vehicle, owner in vehicles:
        # Calcular impuestos para cada vehículo
        tax_calculation = VehicleService.calculate_total_tax_amount(
            vehicle, active_tax_period, tax_rates
        )

        # Obtener último pago
        last_payment = (
            db.query(Payment)
            .filter(Payment.vehicle_id == vehicle.id)
            .order_by(Payment.payment_date.desc())
            .first()
        )

        # Crear respuesta para el dashboard
        dashboard_entry = VehicleTaxResponse(
            vehicle_id=vehicle.id,
            plate=vehicle.plate,
            owner_name=owner.full_name,
            base_tax=tax_calculation["base_tax"],
            traffic_light_fee=tax_calculation["traffic_light_fee"],
            total_amount=tax_calculation["total_amount"],
            tax_status=vehicle.current_tax_status,
            due_date=active_tax_period.due_date,
            last_payment_date=last_payment.payment_date if last_payment else None
        )

        dashboard_data.append(dashboard_entry)

    return dashboard_data


@router.get("/account-statement-data/{plate}", response_model=AccountStatementResponse)
def get_account_statement_data(
        plate: str,
        document_type: str,
        document_number: str,
        db: Session = Depends(get_db)
):
    """Obtiene los datos para el estado de cuenta"""
    details, error = VehicleService.get_vehicle_tax_details(
        db, plate, document_type, document_number
    )
    if error:
        raise HTTPException(status_code=404, detail=error)

    return {
        "header": {
            "title": "GOBERNACIÓN DEL VALLE",
            "subtitle": f"ESTADO DE CUENTA - VEHÍCULO {plate}",
            "date": datetime.now()
        },
        "vehicle_details": details["vehicle_details"],
        "tax_details": details["tax_details"],
        "payment_history": VehicleService.get_payment_history(db, details["vehicle_details"]["id"])
    }


@router.post("/send-statement", response_model=dict)
def send_account_statement(
        request: EmailRequestSchema,
        db: Session = Depends(get_db)
):
    """Envía el estado de cuenta por correo"""
    details, error = VehicleService.get_vehicle_tax_details(
        db, request.plate, request.document_type, request.document_number
    )
    if error:
        raise HTTPException(status_code=404, detail=error)

    # Aquí iría la lógica de envío de correo
    return {
        "message": f"Estado de cuenta enviado a {request.email}",
        "success": True
    }


@router.get("/process-detail/{plate}", response_model=ProcessDetailResponse)
def get_process_detail(
        plate: str,
        document_type: str,
        document_number: str,
        db: Session = Depends(get_db)
):
    """Obtiene el detalle del proceso fiscal"""
    details, error = VehicleService.get_vehicle_tax_details(
        db, plate, document_type, document_number
    )
    if error:
        raise HTTPException(status_code=404, detail=error)

    return {
        "vehicle_info": details["vehicle_details"],
        "pending_payments": VehicleService.get_pending_payments(db, details["vehicle_details"]["id"]),
        "payment_history": VehicleService.get_payment_history(db, details["vehicle_details"]["id"])
    }


@router.get("/banks", response_model=List[PSEBankResponse])
def get_bank_list():
    """Obtiene lista de bancos disponibles para PSE"""
    # Simulación de lista de bancos
    return [
        {"bank_code": "1001", "bank_name": "Bancolombia", "status": "active"},
        {"bank_code": "1002", "bank_name": "Banco de Bogotá", "status": "active"},
        {"bank_code": "1003", "bank_name": "Davivienda", "status": "active"},
        {"bank_code": "1004", "bank_name": "BBVA", "status": "active"}
    ]


@router.post("/initiate-payment", response_model=PSERedirectResponse)
def initiate_payment(
        payment: PSEPaymentRequest,
        db: Session = Depends(get_db)
):
    """Inicia el proceso de pago PSE"""
    # Verificar vehículo y calcular monto
    details, error = VehicleService.get_vehicle_tax_details(
        db, payment.plate, payment.document_type, payment.document_number
    )
    if error:
        raise HTTPException(status_code=404, detail=error)

    try:
        pse_info = PaymentService.initiate_pse_payment(
            db=db,
            vehicle_id=details["vehicle_details"]["id"],
            amount=details["tax_details"]["total_amount"],
            bank_code=payment.bank_code,
            email=payment.email
        )
        return pse_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/complete-payment/{transaction_id}", response_model=PaymentCompletionResponse)
def complete_payment(
        transaction_id: str,
        db: Session = Depends(get_db)
):
    """Completa el proceso de pago PSE"""
    try:
        result = PaymentService.complete_pse_payment(
            db=db,
            transaction_id=transaction_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-status/{transaction_id}", response_model=PaymentCompletionResponse)
def check_payment_status(
        transaction_id: str,
        db: Session = Depends(get_db)
):
    """Verifica el estado de un pago"""
    try:
        status = PaymentService.get_payment_status(
            db=db,
            transaction_id=transaction_id
        )
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
