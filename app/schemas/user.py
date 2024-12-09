from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Esquema base para User
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    employee_id: str
    is_active: bool = True


# Esquema para crear usuario
class UserCreate(UserBase):
    password: str


# Esquema para actualizar usuario
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    fingerprint_template: Optional[str] = None
    is_active: Optional[bool] = None


# Esquema para respuesta de usuario
class User(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
