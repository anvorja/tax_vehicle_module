from datetime import datetime
from fpdf import FPDF
from typing import Dict
import os


class PDFService:
    @staticmethod
    def generate_account_statement(
            vehicle_info: Dict,
            tax_info: Dict,
            filename: str = None
    ) -> str:
        """
        Genera el PDF del estado de cuenta
        Returns: path del archivo generado
        """
        pdf = FPDF()
        pdf.add_page()

        # Configuración de la página
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)

        # Encabezado
        pdf.image("app/static/logo.png", x=10, y=10, w=60)  # Ajusta la ruta y dimensiones
        pdf.cell(0, 10, "GOBERNACIÓN DEL VALLE", align="C", ln=True)
        pdf.cell(0, 10, "ESTADO DE CUENTA - VEHÍCULO " + vehicle_info["plate"], align="C", ln=True)

        # Información General
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "INFORMACIÓN GENERAL", ln=True)
        pdf.set_font("Arial", "", 12)

        info = [
            ["Placa", vehicle_info["plate"]],
            ["Marca", vehicle_info["brand"]],
            ["Modelo", vehicle_info["model"]],
            ["Año", str(vehicle_info["year"])]
        ]

        for item in info:
            pdf.cell(50, 10, item[0] + ":", ln=0)
            pdf.cell(0, 10, item[1], ln=True)

        # Información de Pagos
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "PAGOS", ln=True)
        pdf.set_font("Arial", "", 12)

        headers = ["Vigencia", "Monto", "Estado", "Fecha Límite"]
        col_width = 47

        # Encabezados de la tabla
        for header in headers:
            pdf.cell(col_width, 10, header, 1, 0, "C")
        pdf.ln()

        # Datos de pagos
        payment_data = [
            tax_info["tax_year"],
            f"${tax_info['total_amount']:,.2f}",
            tax_info["tax_status"],
            tax_info["due_date"].strftime("%d/%m/%Y")
        ]

        for item in payment_data:
            pdf.cell(col_width, 10, str(item), 1, 0, "C")
        pdf.ln()

        # Fecha de generación
        pdf.ln(10)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)

        # Generar nombre de archivo si no se proporciona
        if not filename:
            filename = f"estado_cuenta_{vehicle_info['plate']}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"

        # Crear directorio para PDFs si no existe
        os_path = os.path.join("app", "static", "pdfs")
        if not os.path.exists(os_path):
            os.makedirs(os_path)

        filepath = os.path.join(os_path, filename)
        pdf.output(filepath)

        return filepath
