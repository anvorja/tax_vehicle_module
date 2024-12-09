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
import random

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

    # Obtener los tipos de documento
    doc_types = session.query(DocumentType).all()
    if not doc_types:
        logger.error("Document types not found")
        return

    # Crear superadmin primero
    superadmin = User(
        email="admin@example.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superadmin=True,
        document_type_id=doc_types[0].id,  # Asumiendo que CC es el primer tipo de documento
        document_number="1234567890",
        city="Bogotá",
        notification_email="admin@example.com"
    )
    session.add(superadmin)

    # Crear 15 usuarios regulares
    users = [
        {
            "email": f"user{i}@example.com",
            "full_name": f"Usuario Prueba {i}",
            "hashed_password": get_password_hash(f"user{i}pass"),
            "is_active": True,
            "is_superadmin": False,
            "document_type_id": random.choice(doc_types).id,
            "document_number": f"10{i:08d}",
            "city": random.choice(["Bogotá", "Cali", "Medellín", "Buga", "Pasto"]),
            "notification_email": f"user{i}@example.com",
            "phone": f"310{i:07d}"
        }
        for i in range(1, 16)
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
        ("Toyota", ["Corolla", "Camry", "RAV4", "Prado", "Yaris", "Hilux"]),
        ("Chevrolet", ["Spark", "Cruze", "Captiva", "Tracker", "Onix", "Sail"]),
        ("Mazda", ["3", "CX-30", "CX-5", "6", "CX-9", "MX-5"]),
        ("Renault", ["Logan", "Duster", "Sandero", "Koleos", "Clio", "Megane"]),
        ("Tesla", ["Model 3", "Model Y", "Model S", "Model X", "Cybertruck"]),
        ("Ford", ["Fiesta", "Focus", "Mustang", "Escape", "Explorer", "F-150"]),
        ("Honda", ["Civic", "Accord", "CR-V", "Fit", "HR-V", "Odyssey"]),
        ("Nissan", ["Versa", "Sentra", "Altima", "Rogue", "Pathfinder", "Frontier"]),
        ("BMW", ["3 Series", "5 Series", "X3", "X5", "i3", "i8"]),
        ("Mercedes-Benz", ["A-Class", "C-Class", "E-Class", "GLE", "GLC", "S-Class"]),
        ("Yamaha", ["YZF-R3", "MT-03", "XSR155", "FZ-S", "FZ25", "FZ-X"]),
        ("Honda", ["CBR150R", "CBR250R", "CBR650R", "CBR1000RR", "CB500F", "CB650F"]),
        ("Suzuki", ["GSX-R150", "GSX-R600", "GSX-R750", "GSX-R1000", "GSX-S1000", "GSX-S750"]),
        ("Kawasaki", ["Ninja 300", "Ninja 400", "Ninja 650", "Ninja ZX-6R", "Ninja ZX-10R", "Ninja H2"]),
        ("Ducati", ["Monster 797", "Monster 821", "Monster 1200", "Panigale V2", "Panigale V4", "Streetfighter V4"])
    ]

    vehicles = []
    for i in range(45):
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
        base_value = 40_000_000 + (i * 3_000_000)

        # Determinar tipo de vehículo
        vehicle_type = random.choice([VehicleType.PARTICULAR, VehicleType.PUBLIC, VehicleType.MOTORCYCLE])

        vehicle_data = {
            "plate": plate,
            "brand": brand,
            "model": model,
            "year": random.randint(1995, 2024),  # Años entre 1995 y 2024
            "vehicle_type": vehicle_type,
            "commercial_value": base_value,
            "is_electric": is_electric,
            "is_hybrid": not is_electric and i % 3 == 0,  # Algunos híbridos
            "registration_date": date(random.randint(1995, 2024), random.randint(1, 12), random.randint(1, 28)),
            "city": random.choice(["Bogotá", "Cali", "Medellín", "Buga", "Pasto"]),
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
