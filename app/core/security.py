# app/core/security.py
from datetime import datetime, timedelta
from typing import Union, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.core.config import settings

# Configuración del contexto de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
        subject: Union[str, Any],
        expires_delta: timedelta | None = None
) -> str:
    """
    Crea un token JWT de acceso
    Args:
        subject: Identificador del usuario (normalmente user.id)
        expires_delta: Tiempo de expiración opcional
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": str(subject)
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """
    Verifica y decodifica un token JWT
    Raises:
        JWTError: Si el token es inválido o ha expirado
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return decoded_token
    except JWTError:
        raise


def get_password_hash(password: str) -> str:
    """
    Genera el hash de una contraseña usando bcrypt
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash
    """
    return pwd_context.verify(plain_password, hashed_password)
