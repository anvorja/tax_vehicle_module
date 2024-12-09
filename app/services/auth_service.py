from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña es correcta"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Genera un hash de la contraseña"""
        return pwd_context.hash(password)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Autentica un usuario por email y contraseña"""
        user = self.get_user_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token JWT"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {
            "sub": str(user_id),
            "exp": expire
        }
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    def decode_token(self, token: str) -> Optional[int]:
        """Decodifica un token JWT y retorna el user_id"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id = int(payload.get("sub"))
            return user_id
        except JWTError:
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por su ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def update_last_login(self, user: User) -> None:
        """Actualiza la fecha del último login"""
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        self.db.commit()

    def increment_failed_attempts(self, user: User) -> None:
        """Incrementa el contador de intentos fallidos"""
        user.failed_login_attempts += 1
        self.db.commit()

    def verify_token(self, token: str) -> Optional[User]:
        """Verifica un token y retorna el usuario si es válido"""
        user_id = self.decode_token(token)
        if user_id is None:
            return None

        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        if not user.is_active:
            return None

        return user

    def is_token_valid(self, token: str) -> bool:
        """Verifica si un token es válido"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            exp = payload.get("exp")
            if exp is None:
                return False
            return datetime.fromtimestamp(exp) > datetime.utcnow()
        except JWTError:
            return False

    def get_current_user(self, token: str) -> Optional[User]:
        """Obtiene el usuario actual basado en el token"""
        user = self.verify_token(token)
        if user is None:
            return None
        return user

    def check_superadmin(self, user: User) -> bool:
        """Verifica si el usuario es superadmin"""
        return user.is_superadmin
