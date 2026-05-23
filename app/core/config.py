"""
OpsPilot — Application Configuration.

Centralised, env-driven settings using Pydantic Settings.
Every configurable value lives here — no magic strings scattered
throughout the codebase.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Paths ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """
    Application-wide settings, loaded from environment variables
    and/or a `.env` file at the project root.
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "OpsPilot"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True

    # ── Server ───────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OpenAI (future) ──────────────────────────────────────
    OPENAI_API_KEY: str | None = None

    # ── Paystack (future) ────────────────────────────────────
    PAYSTACK_SECRET_KEY: str | None = None
    PAYSTACK_PUBLIC_KEY: str | None = None

    # ── Validators ───────────────────────────────────────────
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── Computed helpers ─────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == Environment.TESTING


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
