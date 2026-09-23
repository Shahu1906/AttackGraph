"""
AttackGraphX API Gateway — Application Configuration
Loads settings from .env file using pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # JWT
    jwt_secret: str = "INSECURE_DEFAULT_CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # Analysis Service (upstream)
    analysis_service_url: str = "http://localhost:9000"
    analysis_timeout: float = 10.0
    analysis_retries: int = 3

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 300

    # CORS
    frontend_origin: str = "http://localhost:5173"


@lru_cache()
def get_settings() -> Settings:
    """Return the process-wide settings instance loaded from environment configuration."""
    return Settings()
