from datetime import date, timedelta, datetime
from typing import Optional, Tuple, Dict

from sqlalchemy.orm import Session

from app.models import TaxPeriod, User, Payment
from app.models.payment import PaymentStatus
from app.models.vehicle import Vehicle, VehicleType
from app.models.tax_rate import TaxRate
from app.services.document_service import DocumentService
from app.services.tax_service import TaxService


class VehicleService:
    @staticmethod
    def check_discount_eligibility(vehicle: Vehicle) -> bool:
        """Verifica si un vehículo es elegible para descuentos ambientales"""
        if not vehicle or not isinstance(vehicle, Vehicle):
            return False

        return (vehicle.is_electric or vehicle.is_hybrid) and \
            (not vehicle.discount_expiry or vehicle.discount_expiry > date.today())

    @staticmethod
    def calculate_tax_rate(vehicle: Vehicle, tax_rate: TaxRate) -> float:
        """Calcula la tasa de impuesto aplicable considerando descuentos ambientales"""
        if not vehicle or not tax_rate:
            return 0.0

        base_rate = tax_rate.rate + tax_rate.additional_rate

        if VehicleService.check_discount_eligibility(vehicle):
            if vehicle.is_electric:
                return base_rate * 0.4  # 60% descuento
            return base_rate * 0.6  # 40% descuento para híbridos

        return base_rate

    @staticmethod
    def validate_vehicle_data(vehicle: Vehicle) -> tuple[bool, list[str]]:
        """Validar los datos del vehículo"""
        errors = []

        if vehicle.is_electric and vehicle.is_hybrid:
            errors.append("Un vehículo no puede ser eléctrico e híbrido simultáneamente")

        if vehicle.year > date.today().year:
            errors.append("El año del vehículo no puede ser futuro")

        if vehicle.commercial_value < 0:
            errors.append("El valor comercial no puede ser negativo")

        return len(errors) == 0, errors

    @staticmethod
    def calculate_tax_amount(vehicle: Vehicle, tax_period: TaxPeriod, tax_rates: list[TaxRate]) -> float:
        """Calcula el monto total del impuesto"""
        if not vehicle or not tax_period:
            return 0.0

        # Obtener tasa base según avalúo
        applicable_rate = TaxService.get_applicable_tax_rate(vehicle.commercial_value, tax_rates)
        if not applicable_rate:
            return 0.0

        # Convertir la tasa de porcentaje a decimal (1.5% to 0.015)
        base_rate = applicable_rate.rate / 100.0

        # Calcular impuesto base (sin descuentos)
        base_tax = vehicle.commercial_value * base_rate

        # Aplicar descuentos para vehículos eléctricos/híbridos
        if vehicle.is_electric:
            # Para eléctricos, el impuesto no puede superar el 1% del valor comercial
            max_tax = vehicle.commercial_value * 0.01
            base_tax = min(base_tax, max_tax)

            if vehicle.vehicle_type == VehicleType.PUBLIC:
                base_tax *= 0.3  # 70% descuento para taxis eléctricos
            else:
                base_tax *= 0.4  # 60% descuento para eléctricos particulares
        elif vehicle.is_hybrid:
            base_tax *= 0.6  # 40% descuento para híbridos

        # Si es vehículo nuevo, prorratear por meses restantes
        if vehicle.is_new:
            remaining_months = 12 - vehicle.registration_date.month + 1
            base_tax = (base_tax / 12) * remaining_months

        return round(base_tax, 2)

    @staticmethod
    def calculate_total_tax_amount(vehicle: Vehicle, tax_period: TaxPeriod, tax_rates: list[TaxRate]) -> dict:
        """Calcula el desglose completo del impuesto"""
        base_tax = VehicleService.calculate_tax_amount(vehicle, tax_period, tax_rates)
        traffic_light_fee = TaxService.calculate_traffic_light_fee(tax_period,
                                                                   vehicle.vehicle_type == VehicleType.MOTORCYCLE)

        return {
            "base_tax": base_tax,
            "traffic_light_fee": traffic_light_fee,
            "total_amount": base_tax + traffic_light_fee
        }

    @staticmethod
    def get_vehicle_tax_details(
            db: Session,
            plate: str,
            document_type: str,
            document_number: str
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Obtiene los detalles del vehículo y su impuesto si los datos coinciden
        Returns: (datos del vehículo y tax, mensaje de error)
        """
        # Validar documento
        if not DocumentService.validate_document_number(document_type, document_number):
            return None, "Número de documento inválido"

        # Buscar vehículo y propietario
        vehicle = (
            db.query(Vehicle)
            .join(User)
            .filter(
                Vehicle.plate == plate.upper(),
                User.document_type_id == document_type,
                User.document_number == document_number
            )
            .first()
        )

        if not vehicle:
            return None, "No se encontró el vehículo con los datos proporcionados"

        # Obtener período fiscal activo y tasas
        tax_period = db.query(TaxPeriod).filter(TaxPeriod.is_active == True).first()
        if not tax_period:
            return None, "No hay período fiscal activo"

        tax_rates = db.query(TaxRate).filter(TaxRate.tax_period_id == tax_period.id).all()

        # Calcular impuestos e información de descuentos
        tax_details = VehicleService.calculate_total_tax_amount(vehicle, tax_period, tax_rates)

        # Calcular información de descuentos
        discount_info = None
        if vehicle.is_electric or vehicle.is_hybrid:
            base_amount = tax_details["pre_discount_amount"] if "pre_discount_amount" in tax_details else 0
            discount_type = None
            discount_percentage = 0

            if vehicle.is_electric:
                if vehicle.vehicle_type == VehicleType.PUBLIC:
                    discount_type = "ELECTRIC_PUBLIC"
                    discount_percentage = 70
                else:
                    discount_type = "ELECTRIC_PRIVATE"
                    discount_percentage = 60
            elif vehicle.is_hybrid:
                discount_type = "HYBRID"
                discount_percentage = 40

            amount_saved = base_amount - tax_details["base_tax"]
            expiry_date = vehicle.registration_date + timedelta(days=365 * 5)

            discount_info = {
                "type": discount_type,
                "percentage": discount_percentage,
                "amount_saved": round(amount_saved, 2),
                "expiry_date": expiry_date
            }

        # Construir respuesta
        response = {
            "vehicle_details": {
                "id": vehicle.id,
                "plate": vehicle.plate,
                "brand": vehicle.brand,
                "model": vehicle.model,
                "year": vehicle.year,
                "type": vehicle.vehicle_type.value,
                "city": vehicle.city,
                "is_electric": vehicle.is_electric,
                "is_hybrid": vehicle.is_hybrid
            },
            "tax_details": {
                "base_tax": tax_details["base_tax"],
                "traffic_light_fee": tax_details["traffic_light_fee"],
                "total_amount": tax_details["total_amount"],
                "due_date": tax_period.due_date,
                "tax_status": vehicle.current_tax_status.value,
                "has_pending_payments": vehicle.has_pending_payments,
                "last_payment_date": vehicle.last_payment_date
            },
            "discounts": discount_info
        }

        return response, None

    @staticmethod
    def get_payment_history(db: Session, vehicle_id: int) -> list[dict]:
        """Obtiene el historial de pagos"""
        payments = (
            db.query(Payment)
            .filter(Payment.vehicle_id == vehicle_id)
            .order_by(Payment.payment_date.desc())
            .all()
        )

        return [
            {
                "payment_date": payment.payment_date,
                "amount": payment.amount,
                "status": payment.status.value,
                "invoice_number": payment.invoice_number,
                "tax_year": payment.tax_year
            }
            for payment in payments
        ]

    @staticmethod
    def get_pending_payments(db: Session, vehicle_id: int) -> list[dict]:
        """Obtiene los pagos pendientes"""
        payments = (
            db.query(Payment)
            .filter(
                Payment.vehicle_id == vehicle_id,
                Payment.status == PaymentStatus.PENDING
            )
            .order_by(Payment.due_date.asc())
            .all()
        )

        return [
            {
                "vigencia": payment.tax_year,
                "proceso_fiscal": f"Etapa {1}",  # Esto podría venir de otra tabla
                "monto": payment.amount,
                "fecha_limite": payment.due_date,
                "seleccionable": True
            }
            for payment in payments
        ]

    @staticmethod
    def get_vehicle_payment_history(
            db: Session,
            plate: str,
            document_type: str,
            document_number: str
    ) -> Dict:
        """Obtiene el historial completo de pagos de un vehículo"""
        vehicle = (
            db.query(Vehicle)
            .join(User)
            .filter(
                Vehicle.plate == plate.upper(),
                User.document_type_id == document_type,
                User.document_number == document_number
            )
            .first()
        )

        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        # Obtener el último pago completado
        ultimo_pago = (
            db.query(Payment)
            .filter(
                Payment.vehicle_id == vehicle.id,
                Payment.status == PaymentStatus.COMPLETED
            )
            .order_by(Payment.payment_date.desc())
            .first()
        )

        # Obtener historial de pagos
        pagos = (
            db.query(Payment)
            .filter(Payment.vehicle_id == vehicle.id)
            .order_by(Payment.tax_year.desc(), Payment.payment_date.desc())
            .all()
        )

        return {
            "vehicle_info": {
                "periodo_certificacion": datetime.now().year,
                "fecha_consulta": datetime.now().strftime("%Y-%m-%d"),
                "placa": vehicle.plate,
                "marca": vehicle.brand
            },
            "ultimo_pago": {
                "periodo_pagado": ultimo_pago.tax_year if ultimo_pago else None,
                "fecha_pago": ultimo_pago.payment_date.strftime("%Y-%m-%d") if ultimo_pago else None,
                "valor_pagado": ultimo_pago.amount if ultimo_pago else 0.0
            },
            "historial_pagos": [
                {
                    "año": pago.tax_year,
                    "concepto": "Impuesto Vehicular",
                    "valor": pago.amount,
                    "estado": "Pagado" if pago.status == PaymentStatus.COMPLETED else "Pendiente"
                }
                for pago in pagos
            ]
        }
