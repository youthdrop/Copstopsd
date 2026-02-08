from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.router import router as api_router


# ---------------------------------------
# App
# ---------------------------------------
app = FastAPI(
    title="Police Accountability API",
    version="0.1.0",
)


# ---------------------------------------
# CORS (Local + custom domain + Vercel)
# ---------------------------------------
# Always-allowed dev origins
DEV_ORIGINS: List[str] = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://localhost:3000",
]

# Always-allowed prod origins (your custom domain)
PROD_ORIGINS: List[str] = [
    "https://copstopsd.org",
    "https://www.copstopsd.org",
]

# Optional: Railway env var CORS_ORIGINS="https://copstopsd.org,https://www.copstopsd.org"
env_origins = (os.getenv("CORS_ORIGINS") or "").strip()
ENV_ORIGINS: List[str] = [o.strip() for o in env_origins.split(",") if o.strip()] if env_origins else []

# Optional: a single explicit frontend URL
# Example: FRONTEND_URL="https://your-app.vercel.app"
frontend_url = (os.getenv("FRONTEND_URL") or "").strip()
FRONTEND_ORIGINS: List[str] = [frontend_url] if frontend_url else []

# From your settings helper (comma-separated or list)
settings_origins = settings.cors_list() or []

# Merge + de-dupe
merged: List[str] = []
seen = set()

for o in (PROD_ORIGINS + DEV_ORIGINS + ENV_ORIGINS + FRONTEND_ORIGINS + settings_origins):
    if not o:
        continue
    o = o.strip()
    if o and o not in seen:
        seen.add(o)
        merged.append(o)

# Allow Vercel preview domains (wildcards not supported in allow_origins)
vercel_origin_regex = r"^https:\/\/([a-z0-9-]+\.)*vercel\.app$"

# If "*" configured anywhere, you cannot use credentials
if "*" in seen:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=merged,
        allow_origin_regex=vercel_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],  # must allow Content-Type, Authorization, X-Staff-Key
    )


# ---------------------------------------
# Global error handler
# ---------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {type(exc).__name__}: {exc}"},
    )


# ---------------------------------------
# API routes
# ---------------------------------------
app.include_router(api_router)


# ---------------------------------------
# Health check (Railway)
# ---------------------------------------
@app.get("/health")
def health():
    return {"ok": True}
