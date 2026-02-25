"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe env var parsing.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars!!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./students.db"

    # ML
    MODEL_DIR: str = "./ml/models"
    MODEL_REGISTRY_PATH: str = "./ml/models/model_registry.json"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
