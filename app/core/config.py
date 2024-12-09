from typing import List

from pydantic.v1 import validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Any, Dict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vehicle Tax Payment System"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"  # Valor por defecto común para JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20  # 20 minutos como especificado

    FRONTEND_URL: str

    # Configuración de correo
    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [self.FRONTEND_URL]

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: str | None, values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"

    @validator("SECRET_KEY")
    def secret_key_must_be_secure(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")
        return v

    model_config = SettingsConfigDict(env_file='.env', case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()