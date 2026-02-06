from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/police_accountability"
    CORS_ORIGINS: str = "http://localhost:5173"
    UPLOAD_DIR: str = "./data/uploads"

    EMAIL_FROM: str = "alerts@potc.local"
    EMAIL_TO: str = "laila@potcsd.org"
    EMAIL_MODE: str = "console"  # console | smtp
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

settings = Settings()
