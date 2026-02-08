from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router as api_router

app = FastAPI(title="Police Accountability API", version="0.1.0")

# -------------------------
# CORS
# -------------------------
origins: List[str] = [
    "https://copstopsd.org",
    "https://www.copstopsd.org",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Optional: Railway env var
# CORS_ORIGINS="https://copstopsd.org,https://www.copstopsd.org"
env_origins = (os.getenv("CORS_ORIGINS") or "").strip()
if env_origins:
    origins = [o.strip() for o in env_origins.split(",") if o.strip()]

# Allow Vercel preview domains if needed
vercel_origin_regex = r"^https:\/\/([a-z0-9-]+\.)*vercel\.app$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=vercel_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # must allow Content-Type, Authorization, X-Staff-Key
)

# -------------------------
# HARD STOP: Always succeed OPTIONS (fixes preflight 400)
# -------------------------
@app.options("/{full_path:path}")
def preflight(full_path: str):
    return Response(status_code=204)

# -------------------------
# Error handler
# -------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {type(exc).__name__}: {exc}"},
    )

# -------------------------
# Routes
# -------------------------
app.include_router(api_router)

@app.get("/health")
def health():
    return {"ok": True}
