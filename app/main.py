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


app = FastAPI(
    title="Police Accountability API",
    version="0.1.0",
)

# ---------------------------------------
# CORS (Local + Vercel + custom domains)
# ---------------------------------------
# Keep your dev origins
VITE_ORIGINS: List[str] = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://localhost:3000",
]

# Pull configured origins from settings (comma-separated)
settings_origins = settings.cors_list() or []

# Merge, de-dupe, and normalize
merged: List[str] = []
seen = set()

for o in (settings_origins + VITE_ORIGINS):
    if not o:
        continue
    o = o.strip()
    if o and o not in seen:
        seen.add(o)
        merged.append(o)

# OPTIONAL: allow a single explicit frontend URL (recommended)
# Example Railway variable: FRONTEND_URL=https://your-app.vercel.app
frontend_url = (os.getenv("FRONTEND_URL") or "").strip()
if frontend_url and frontend_url not in seen:
    merged.append(frontend_url)
    seen.add(frontend_url)

# Vercel preview domains must be allowed via regex (wildcards not supported in allow_origins)
# This regex allows:
# - https://anything.vercel.app
# - https://anything-username.vercel.app
vercel_origin_regex = r"^https:\/\/([a-z0-9-]+\.)*vercel\.app$"

# If someone configured "*" in settings, you cannot use credentials with it.
# We preserve your safety behavior from the current file. :contentReference[oaicite:1]{index=1}
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
        allow_origin_regex=vercel_origin_regex,  # ✅ makes Vercel work
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------
# Global error handler (keeps your current behavior)
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
