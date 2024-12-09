# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, vehicles_endpoints, payments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

api_router.include_router(vehicles_endpoints.router, prefix="/vehicles", tags=["Vehicles"])

api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
