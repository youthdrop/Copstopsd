from __future__ import annotations

import os
from typing import List, Optional
from pydantic import BaseSettings


def normalize_db_url(url: str) -> str:
    """
    Railway may provide:
      postgres://user:pass@host/db

    SQLAlchemy + psycopg3 requires:
      postgresql+psycopg://user:pass@host/db
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


class Settings(BaseSettings):
    # -------------------
    # Environment
    # -------------------
    ENV: str = os.getenv("ENV", "development")

    # -------------------
    # Security
    # -------------------
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-change-this-secret")
    PUBLIC_INTAKE_KEY: str = os.getenv(
        "PUBLIC_INTAKE_KEY", "dev-public-intake-key-change-me"
    )

    # -------------------
    # Database
    # -------------------
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # -------------------
    # CORS
    # -------------------
    # Comma-separated list of allowed origins
    # Example:
    #   http://localhost:5173,https://copstopsd.vercel.app
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    )

    # -------------------
    # Email (optional)
    # -------------------
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL: Optional[str] = os.getenv("FROM_EMAIL")
    STAFF_NOTIFICATION_EMAIL: Optional[str] = os.getenv(
        "STAFF_NOTIFICATION_EMAIL"
    )

    # -------------------
    # Auth / OTP
    # -------------------
    RESET_OTP_EXPIRE_MINUTES: int = int(
        os.getenv("RESET_OTP_EXPIRE_MINUTES", "10")
    )

    class Config:
        case_sensitive = True

    # -------------------
    # Helpers
    # -------------------
    def cors_list(self) -> List[str]:
        """
        Returns cleaned list of allowed CORS origins.
        """
        if not self.CORS_ORIGINS:
            return []

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()

# -------------------
# Final validation / normalization
# -------------------
if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set (required for Railway)")

settings.DATABASE_URL = normalize_db_url(settings.DATABASE_URL)
