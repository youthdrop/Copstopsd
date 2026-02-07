# app/db/session.py
from __future__ import annotations

import os
from typing import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _normalize_db_url(url: str) -> str:
    """
    Normalize DB URL formats for SQLAlchemy.
    - Converts deprecated postgres:// to postgresql://
    - Ensures psycopg v3 driver is used when scheme is postgresql://
    """
    url = (url or "").strip()

    # Heroku-style / old scheme
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    # If no explicit driver given, use psycopg (v3) which you're already using (psycopg)
    # Only rewrite when the URL is plain postgresql:// (no +driver specified)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


db_url_raw = getattr(settings, "DATABASE_URL", "") or ""
db_url = _normalize_db_url(db_url_raw)

if not db_url:
    raise RuntimeError(
        "DATABASE_URL is empty. Set DATABASE_URL in Railway → Backend service → Variables."
    )

# Optional safe debug logging (no password)
# Enable by setting Railway variable: DEBUG_DB=1
if (os.getenv("DEBUG_DB") or "").strip() == "1":
    p = urlparse(db_url)
    print("DATABASE_URL set? True")
    print("DB hostname:", p.hostname)
    print("DB port:", p.port)
    print("DB name:", p.path)

engine = create_engine(
    db_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
