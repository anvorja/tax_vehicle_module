# Vehicle Tax Payment System

A FastAPI-based system for managing vehicle tax payments, designed for government entities to handle vehicle registration, tax calculation, and payment processing.

## System Overview

The Vehicle Tax Payment System is designed to manage the complete lifecycle of vehicle tax payments with the following components:

### User System

- Complete user profile management
- Personal data (name, email, document, phone, address)
- Security (hashed passwords and role-based access)
- Separate notification email for communications

### Vehicle System

- Detailed vehicle registration with unique plate identification
- Classification by type: PARTICULAR, PUBLIC, MOTORCYCLE
- Special characteristics tracking for electric/hybrid vehicles (for discounts)
- Fiscal tracking:
  - Commercial value
  - Tax rate
  - Payment status
  - Payment dates

### Fiscal Period System (TaxPeriod)

- Defines fiscal periods with:
  - Start and end dates
  - Payment due date
  - Traffic light fees
  - UVT (Tax Value Unit) values
  - Minimum penalties

### Tax Rate System (TaxRate)

- Defines tax rates based on:
  - Vehicle type
  - Value range (min_value, max_value)
  - Fiscal year
  - Applicable rate

### Payment System

- Complete transaction recording
- Multiple processing statuses
- Correction tracking
- Management of:
  - Fines
  - Penalties
  - Traffic light fees
  - Bank references

### Payment Tracking System (PaymentStatusLog)

- Complete audit of payment changes
- User tracking for changes
- Detailed timestamps for each change

## System Features

- Designed for vehicle tax management
- Complete payment lifecycle management
- Special vehicle discount system
- Detailed status and change tracking
- Support for corrections and adjustments
- Banking system integration (PSE)
- Penalty and fine calculation

## Installation and Setup

### Prerequisites

- Python 3.8+
- PostgreSQL

### Environment Setup

1. Create a virtual environment:
   
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure the database connection:
   Create a `.env` file with the following content:
   
   ```
   # Database
   POSTGRES_SERVER=localhost
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=somepassword
   POSTGRES_DB=tax_vehicle_db
   DATABASE_URL=postgresql://postgres:somepassword@localhost:5432/tax_vehicle_db
   ```

# JWT Settings

SECRET_KEY=anyToken
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=20
FRONTEND_URL=http://localhost:5173

```
### Database Migration Setup
1. Handle the Alembic configuration:
```bash
# If alembic is already initialized:
# Move the env.py file out of the alembic directory
# Delete the alembic directory and alembic.ini
# Then initialize alembic again:
alembic init alembic
# Replace the generated env.py with the original one
```

2. Run the migrations:
   
   ```bash
   alembic revision --autogenerate -m "Creacion de tablas"
   alembic upgrade head
   ```

3. Seed the database:
   
   ```bash
   python -m app.db.seed-script
   ```

### Starting the Application

```bash
uvicorn app.main:app --reload
```

Visit: http://127.0.0.1:8000/docs

## Authentication

Use the following credentials to access the system:

### Admin Account

- Email: admin@example.com
- Password: admin123

### Test User Account

- Email: user1@example.com
- Password: user1pass

## API Usage Examples

### Login

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=admin@example.com&password=admin123
```

### Vehicle Consultation

```
GET /api/v1/vehicles/consult
plate=ABC004
document_type=3
document_number=1000000004
```

### Initiate Payment

```json
POST /api/v1/payments/initiate
Content-Type: application/json

{
  "plate": "ABC004",
  "document_type": "3",
  "document_number": "1000000004",
  "bank_code": "1002",
  "email": "unemail@gmail.com"
}
```

## Project Structure

```
project/
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── payments.py
│   │       │   └── vehicles.py
│   │       ├── __init__.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── __init__.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   ├── __init__.py
│   │   ├── session.py
│   │   └── seed-script.py
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── payment.py
│   │   ├── user.py
│   │   └── vehicle.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── payment.py
│   │   ├── user.py
│   │   └── vehicle.py
│   └── services/
│       ├── auth.py
│       ├── __init__.py
│       ├── tax_calculator.py
│       └── vehicle.py
└── requirements.txt
```
