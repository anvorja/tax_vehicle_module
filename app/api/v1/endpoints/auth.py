from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.security import (
    create_access_token,
    verify_password
)
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=dict)
async def login(
        db: Session = Depends(deps.get_db),
        form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Iniciar sesión para obtener token de acceso
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar contraseña
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar si el usuario está activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )

    # Crear token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    # Actualizar último login
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/test-token", response_model=dict)
async def test_token(
        current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Probar token de acceso
    """
    return {
        "email": current_user.email,
        "is_superadmin": current_user.is_superadmin,
        "full_name": current_user.full_name
    }


@router.post("/logout")
async def logout(
        current_user: User = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db)
) -> dict:
    """
    Cerrar sesión (para fines de registro, ya que JWT no puede ser invalidado)
    """
    # Actualizar última actividad del usuario
    current_user.last_login = datetime.utcnow()
    db.commit()

    return {"message": "Sesión cerrada exitosamente"}
