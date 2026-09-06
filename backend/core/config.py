"""Configuración de la aplicación vía variables de entorno."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_PATH, extra="ignore")

    ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500"

    REDIS_URL: str = "redis://localhost:6379/0"

    SESSION_IDLE_TTL_SECONDS: int = 1800
    SESSION_ABSOLUTE_TTL_SECONDS: int = 604800
    SESSION_REVOKED_TOMBSTONE_TTL_SECONDS: int = 60
    SESSION_COOKIE_NAME: str = "sid"
    CSRF_COOKIE_NAME: str = "XSRF-TOKEN"
    CSRF_HEADER_NAME: str = "X-XSRF-TOKEN"

    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "5/1minutes"

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def cookie_samesite(self) -> str:
        return "none" if self.is_production else "lax"


settings = Settings()
