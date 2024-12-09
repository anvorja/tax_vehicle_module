# app/core/constants.py
from decimal import Decimal

# Constantes del sistema
MONTHS_IN_YEAR = 12
MAX_PENALTY_PERCENTAGE = Decimal('1.0')  # 100%
MONTHLY_LATE_FEE_RATE = Decimal('0.015')  # 1.5%


# Claves de configuración
class ConfigKeys:
    ELECTRIC_VEHICLE_DISCOUNT = "ELECTRIC_VEHICLE_DISCOUNT"
    ELECTRIC_TAXI_DISCOUNT = "ELECTRIC_TAXI_DISCOUNT"
    HYBRID_VEHICLE_DISCOUNT = "HYBRID_VEHICLE_DISCOUNT"
    MIN_PENALTY_UVT = "MIN_PENALTY_UVT"
    UVT_VALUE = "UVT_VALUE"
    TRAFFIC_LIGHT_FEE = "TRAFFIC_LIGHT_FEE"


################################################################

# Valores impositivos 2024
UVT_VALUE = 47065.0  # Valor UVT 2024
TRAFFIC_LIGHT_FEE = 87000.0  # 2 SMDLV para 2024
MIN_PENALTY_UVT = 7  # Sanción mínima en UVT
LATE_PAYMENT_RATE = 1.5  # Tasa mensual de mora (1.5%)
CORRECTION_PENALTY_RATE = 10.0  # Tasa de sanción por corrección (10%)

# Fechas límite de pago 2024
PAYMENT_DEADLINES = {
    "000-333": "2024-04-30",
    "334-666": "2024-05-31",
    "667-999": "2024-06-28"
}

# Descuentos vehículos
ELECTRIC_VEHICLE_DISCOUNT = 60.0  # 60% descuento
ELECTRIC_TAXI_DISCOUNT = 70.0  # 70% descuento
HYBRID_VEHICLE_DISCOUNT = 40.0  # 40% descuento
