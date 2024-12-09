from datetime import datetime
from sqlalchemy.orm import Session

from app.models import PaymentStatusLog, TaxPeriod
from app.models.payment import Payment, PaymentStatus, PaymentProcessStatus
from app.models.vehicle import Vehicle, TaxStatus


class PaymentService:

    @staticmethod
    def initiate_pse_payment(
            db: Session,
            vehicle_id: int,
            amount: float,
            bank_code: str,
            email: str
    ) -> dict:
        """Inicia un pago PSE"""
        try:
            # Obtener el período fiscal activo
            tax_period = db.query(TaxPeriod).filter(TaxPeriod.is_active == True).first()
            if not tax_period:
                raise ValueError("No hay período fiscal activo")

            # Verificar si existe un pago COMPLETADO
            completed_payment = (
                db.query(Payment)
                .filter(
                    Payment.vehicle_id == vehicle_id,
                    Payment.tax_period_id == tax_period.id,
                    Payment.status == PaymentStatus.COMPLETED
                )
                .first()
            )

            if completed_payment:
                return {
                    "message": "Ya existe un pago completado para este vehículo en el período actual",
                    "transaction_id": completed_payment.pse_transaction_id,
                    "status": PaymentStatus.COMPLETED.value,
                    "payment_date": completed_payment.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": completed_payment.amount,
                    "reference_number": completed_payment.bank_reference
                }

            # Verificar si existe un pago EN CURSO
            pending_payment = (
                db.query(Payment)
                .filter(
                    Payment.vehicle_id == vehicle_id,
                    Payment.tax_period_id == tax_period.id,
                    Payment.status == PaymentStatus.PENDING,
                    Payment.process_status == PaymentProcessStatus.PENDING_PSE
                )
                .first()
            )

            if pending_payment:
                return {
                    "message": "Ya existe un pago en curso para este vehículo",
                    "transaction_id": pending_payment.pse_transaction_id,
                    "status": pending_payment.process_status.value,
                    "amount": pending_payment.amount,
                    "reference_number": pending_payment.bank_reference,
                }

            reference_number = f"PSE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{vehicle_id}"
            payment = Payment(
                vehicle_id=vehicle_id,
                amount=amount,
                tax_year=datetime.now().year,
                payment_method="PSE",
                bank=bank_code,
                process_status=PaymentProcessStatus.PENDING_PSE,
                status=PaymentStatus.PENDING,
                payment_date=datetime.now(),
                due_date=tax_period.due_date,
                pse_transaction_id=reference_number,
                invoice_number=f"INV-{reference_number}",
                bank_reference=reference_number,
                tax_period_id=tax_period.id
            )

            # Crear registro de estado
            payment_log = PaymentStatusLog(
                payment=payment,
                status=PaymentProcessStatus.PENDING_PSE,
                details=f"Pago PSE iniciado banco: {bank_code}, email: {email}",
                timestamp=datetime.now()
            )

            db.add(payment)
            db.add(payment_log)
            db.commit()
            db.refresh(payment)

            return {
                "transaction_id": reference_number,
                "amount": amount,
                "status": payment.process_status.value,
                "reference_number": reference_number
            }

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def complete_pse_payment(
            db: Session,
            transaction_id: str,
            status: str = "SUCCESS"
    ) -> dict:
        """Completa un pago PSE"""
        payment = db.query(Payment).filter(
            Payment.pse_transaction_id == transaction_id
        ).first()

        if not payment:
            raise ValueError("Transacción no encontrada")

        # Verificar si el pago ya fue completado
        if payment.status == PaymentStatus.COMPLETED:
            return {
                "message": "Este pago ya fue completado anteriormente",
                "transaction_id": transaction_id,
                "status": payment.status.value,
                "payment_date": payment.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": payment.amount,
                "reference_number": payment.bank_reference
            }

        try:
            if status == "SUCCESS":
                payment.process_status = PaymentProcessStatus.COMPLETED
                payment.status = PaymentStatus.COMPLETED
                payment.paid_at = datetime.now()

                # Actualizar estado del vehículo
                vehicle = db.query(Vehicle).filter(Vehicle.id == payment.vehicle_id).first()
                vehicle.last_payment_date = datetime.now()
                vehicle.has_pending_payments = False
                vehicle.current_tax_status = TaxStatus.UP_TO_DATE

                log_details = "Pago completado exitosamente"
            else:
                payment.status = PaymentStatus.FAILED
                payment.process_status = PaymentProcessStatus.FAILED
                log_details = f"Pago fallido: {status}"

            # Registrar log de completación
            payment_log = PaymentStatusLog(
                payment=payment,
                status=payment.process_status,
                details=log_details,
                timestamp=datetime.now()
            )

            db.add(payment_log)
            db.commit()
            db.refresh(payment)

            return {
                "transaction_id": transaction_id,
                "status": payment.status.value,
                "payment_date": payment.paid_at.strftime("%Y-%m-%d %H:%M:%S") if payment.paid_at else None,
                "amount": payment.amount,
                "reference_number": payment.bank_reference
            }

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_payment_status(
            db: Session,
            transaction_id: str
    ) -> dict:
        """Obtiene el estado actual de un pago"""
        payment = db.query(Payment).filter(
            Payment.pse_transaction_id == transaction_id
        ).first()

        if not payment:
            raise ValueError("Transacción no encontrada")

        # Construir la respuesta base
        response = {
            "transaction_id": transaction_id,
            "status": payment.status.value,
            "amount": payment.amount,
            "reference_number": payment.bank_reference,
            "payment_date": payment.paid_at.strftime("%Y-%m-%d %H:%M:%S") if payment.paid_at else None
        }

        # Agregar mensaje según el estado
        if payment.status == PaymentStatus.COMPLETED:
            response["message"] = "Pago completado"
        elif payment.status == PaymentStatus.PENDING:
            response["message"] = "Pago en curso"
        else:
            response["message"] = "Estado de pago desconocido"

        return response

    @staticmethod
    def get_payment_history(
            db: Session,
            vehicle_id: int
    ) -> list[Payment]:
        """Obtiene el historial de pagos de un vehículo"""
        return (
            db.query(Payment)
            .filter(Payment.vehicle_id == vehicle_id)
            .order_by(Payment.payment_date.desc())
            .all()
        )
