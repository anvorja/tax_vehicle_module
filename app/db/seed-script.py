from sqlalchemy.orm import Session
from app.models import (
    DocumentType,
    User,
    TaxPeriod,
    TaxRate,
    Vehicle,
    VehicleType
)
from app.core.security import get_password_hash
from datetime import date, datetime, timedelta
import logging
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_document_types(session: Session) -> None:
    """Crear tipos de documento básicos"""
    document_types = [
        {"code": "CC", "name": "Cédula de Ciudadanía", "description": "Documento de identidad colombiano"},
        {"code": "CE", "name": "Cédula de Extranjería", "description": "Documento para extranjeros"},
        {"code": "NIT", "name": "NIT", "description": "Número de Identificación Tributaria"},
        {"code": "PP", "name": "Pasaporte", "description": "Pasaporte"}
    ]

    for doc_type in document_types:
        if not session.query(DocumentType).filter(DocumentType.code == doc_type["code"]).first():
            db_doc = DocumentType(**doc_type)
            session.add(db_doc)

    session.commit()
    logger.info("Document types created successfully")


def create_users(session: Session) -> None:
    """Crear usuarios de prueba y superadmin"""
    # Verificar si ya existen usuarios
    if session.query(User).count() > 1:  # > 1 porque podría existir el superadmin
        logger.info("Users already exist")
        return

    # Obtener el tipo de documento CC
    doc_type = session.query(DocumentType).filter(DocumentType.code == "CC").first()
    if not doc_type:
        logger.error("Document type CC not found")
        return

    # Crear superadmin primero
    superadmin = User(
        email="admin@example.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superadmin=True,
        document_type_id=doc_type.id,
        document_number="1234567890",
        city="Bogotá",
        notification_email="admin@example.com"
    )
    session.add(superadmin)

    # Crear 10 usuarios regulares
    users = [
        {
            "email": f"user{i}@example.com",
            "full_name": f"Usuario Prueba {i}",
            "hashed_password": get_password_hash(f"user{i}pass"),
            "is_active": True,
            "is_superadmin": False,
            "document_type_id": doc_type.id,
            "document_number": f"10{i:08d}",
            "city": "Bogotá",
            "notification_email": f"user{i}@example.com",
            "phone": f"310{i:07d}"
        }
        for i in range(1, 11)
    ]

    for user_data in users:
        user = User(**user_data)
        session.add(user)

    session.commit()
    logger.info("Users created successfully")


def create_tax_periods(session: Session) -> None:
    """Crear período fiscal actual"""
    current_year = datetime.now().year

    # Verificar si ya existe el período fiscal actual
    if session.query(TaxPeriod).filter(TaxPeriod.year == current_year).first():
        logger.info(f"Tax period for year {current_year} already exists")
        return

    tax_period = TaxPeriod(
        year=current_year,
        start_date=date(current_year, 1, 1),
        end_date=date(current_year, 12, 31),
        due_date=date(current_year, 6, 30),
        traffic_light_fee=87000.0,  # 2 SMDLV para 2024
        min_penalty_uvt=7,  # 7 UVT para 2024
        uvt_value=47000.0,  # Valor UVT 2024
        is_active=True
    )

    session.add(tax_period)
    session.commit()
    logger.info(f"Tax period for {current_year} created successfully")


def create_tax_rates(session: Session) -> None:
    """Crear tasas de impuesto para diferentes rangos de valor"""
    current_year = datetime.now().year
    tax_period = session.query(TaxPeriod).filter(TaxPeriod.year == current_year, TaxPeriod.is_active == True).first()

    if not tax_period:
        logger.error("Active tax period not found")
        return

    # Verificar si ya existen tasas para el período actual
    if session.query(TaxRate).filter(TaxRate.tax_period_id == tax_period.id).first():
        logger.info(f"Tax rates for period {current_year} already exist")
        return

    tax_rates = [
        {
            "vehicle_type": VehicleType.PARTICULAR,
            "min_value": 0,
            "max_value": 50_000_000,
            "rate": 1.5,
            "year": current_year,
            "tax_period_id": tax_period.id
        },
        {
            "vehicle_type": VehicleType.PARTICULAR,
            "min_value": 50_000_001,
            "max_value": 100_000_000,
            "rate": 2.5,
            "year": current_year,
            "tax_period_id": tax_period.id
        },
        {
            "vehicle_type": VehicleType.PARTICULAR,
            "min_value": 100_000_001,
            "max_value": None,
            "rate": 3.5,
            "year": current_year,
            "tax_period_id": tax_period.id
        },
        {
            "vehicle_type": VehicleType.MOTORCYCLE,
            "min_value": 0,
            "max_value": None,
            "rate": 1.0,
            "year": current_year,
            "tax_period_id": tax_period.id
        }
    ]

    for rate in tax_rates:
        db_rate = TaxRate(**rate)
        session.add(db_rate)

    session.commit()
    logger.info("Tax rates created successfully")


def create_sample_vehicles(session: Session) -> None:
    """Crear vehículos de prueba variados"""
    # Verificar si ya existen vehículos
    if session.query(Vehicle).count() > 0:
        logger.info("Sample vehicles already exist")
        return

    # Obtener todos los usuarios
    users = session.query(User).all()

    # Lista de marcas y modelos para variedad
    vehicle_types = [
        ("Toyota", ["Corolla", "Camry", "RAV4", "Prado"]),
        ("Chevrolet", ["Spark", "Cruze", "Captiva", "Tracker"]),
        ("Mazda", ["3", "CX-30", "CX-5", "6"]),
        ("Renault", ["Logan", "Duster", "Sandero", "Koleos"]),
        ("Tesla", ["Model 3", "Model Y", "Model S", "Model X"])
    ]

    vehicles = []
    for i in range(10):
        # Seleccionar marca y modelo aleatorios
        brand_idx = i % len(vehicle_types)
        brand, models = vehicle_types[brand_idx]
        model = models[i % len(models)]

        # Seleccionar usuario aleatorio (excepto superadmin)
        user = users[i % (len(users) - 1) + 1]  # +1 para saltar el superadmin

        # Generar placa aleatoria
        plate = f"ABC{i + 1:03d}"

        # Determinar si es eléctrico (solo Tesla)
        is_electric = brand == "Tesla"

        # Valor base entre 40 y 150 millones
        base_value = 40_000_000 + (i * 12_000_000)

        vehicle_data = {
            "plate": plate,
            "brand": brand,
            "model": model,
            "year": 2020 + (i % 5),  # Años entre 2020 y 2024
            "vehicle_type": VehicleType.PARTICULAR,
            "commercial_value": base_value,
            "is_electric": is_electric,
            "is_hybrid": not is_electric and i % 3 == 0,  # Algunos híbridos
            "registration_date": date(2020 + (i % 5), 1 + (i % 12), 1 + (i % 28)),
            "city": "Bogotá",
            "owner_id": user.id,
            "current_appraisal": base_value * 0.9,  # 90% del valor comercial
            "appraisal_year": 2024,
            "engine_displacement": 1600 + (i * 200) if not is_electric else None
        }

        vehicle = Vehicle(**vehicle_data)
        session.add(vehicle)

    session.commit()
    logger.info("Sample vehicles created successfully")


def seed_database() -> None:
    """
    Ejecuta todas las funciones de seed en el orden correcto
    """
    session = SessionLocal()
    try:
        create_document_types(session)
        create_users(session)
        create_tax_periods(session)
        create_tax_rates(session)
        create_sample_vehicles(session)

        logger.info("Database seeded successfully!")
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
