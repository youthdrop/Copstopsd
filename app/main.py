from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router as api_router


# ---------------------------------------
# Create ONE FastAPI app
# ---------------------------------------
app = FastAPI(
    title="Police Accountability API",
    version="0.1.0",
)


# ---------------------------------------
# CORS Configuration
# ---------------------------------------
origins: List[str] = [
    "https://copstopsd.org",
    "https://www.copstopsd.org",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Allow Railway environment override
env_origins = os.getenv("CORS_ORIGINS")
if env_origins:
    origins = [o.strip() for o in env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/([a-z0-9-]+\.)*vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------
# Global error handler
# ---------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
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
