from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router as api_router

app = FastAPI(title="Police Accountability API", version="0.1.0")

# Bump this any time you redeploy so we can verify the server updated
APP_BUILD_ID = "CORS_FIX_2026_02_07_2"

# -------------------------
# CORS
# -------------------------
# Allow your known production origins + local dev.
origins: List[str] = [
    "https://copstopsd.org",
    "https://www.copstopsd.org",
    "https://copstopsd-kdm7hfh85-laila-azizs-projects.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Optional: Railway env var override
# Example: CORS_ORIGINS="https://copstopsd.org,https://www.copstopsd.org,https://<your-vercel-app>.vercel.app"
env_origins = (os.getenv("CORS_ORIGINS") or "").strip()
if env_origins:
    origins = [o.strip() for o in env_origins.split(",") if o.strip()]

# Allow Vercel preview domains too (any *.vercel.app)
vercel_origin_regex = r"^https:\/\/.*\.vercel\.app$"

# ✅ IMPORTANT:
# Do NOT define your own @app.options routes.
# CORSMiddleware must handle preflight so it can attach Access-Control-Allow-* headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=vercel_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # includes Content-Type, Authorization, X-Staff-Key
)

# -------------------------
# Error handler (keeps errors readable)
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

@app.get("/build")
def build():
    return {"build": APP_BUILD_ID}
