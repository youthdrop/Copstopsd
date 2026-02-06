from __future__ import annotations

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


def normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Settings(BaseSettings):
    # Environment
    ENV: str = os.getenv("ENV", "development")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-change-this-secret")
    PUBLIC_INTAKE_KEY: str = os.getenv(
        "PUBLIC_INTAKE_KEY", "dev-public-intake-key-change-me"
    )

    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # CORS (comma-separated)
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    )

    # Email (optional)
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL: Optional[str] = os.getenv("FROM_EMAIL")
    STAFF_NOTIFICATION_EMAIL: Optional[str] = os.getenv("STAFF_NOTIFICATION_EMAIL")

    # OTP
    RESET_OTP_EXPIRE_MINUTES: int = int(os.getenv("RESET_OTP_EXPIRE_MINUTES", "10"))

    class Config:
        case_sensitive = True

    def cors_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set (required for Railway)")

settings.DATABASE_URL = normalize_db_url(settings.DATABASE_URL)
