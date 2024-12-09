from app.models.tax_rate import TaxRate
from app.models.tax_period import TaxPeriod


class TaxService:
    @staticmethod
    def get_applicable_tax_rate(value: float, tax_rates: list[TaxRate]) -> TaxRate | None:
        """Determina la tasa de impuesto aplicable según el valor del vehículo"""
        if not tax_rates:
            return None

        for rate in tax_rates:
            min_val = rate.min_value or float('-inf')
            max_val = rate.max_value or float('inf')

            if min_val <= value <= max_val:
                return rate

        return None

    @staticmethod
    def calculate_traffic_light_fee(tax_period: TaxPeriod, is_motorcycle: bool) -> float:
        """Calcula la tarifa de semaforización"""
        if not tax_period:
            return 0.0

        if is_motorcycle:
            return tax_period.traffic_light_fee * 0.5  # 50% para motos

        return tax_period.traffic_light_fee
