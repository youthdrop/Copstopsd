from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.router import router as api_router


app = FastAPI(
    title="Police Accountability API",
    version="0.1.0",
)

# ✅ Always allow both localhost + 127 for Vite dev server
VITE_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

# ✅ Merge with settings.cors_list() (instead of replacing it)
settings_origins = settings.cors_list() or []
merged = []
seen = set()

for o in (settings_origins + VITE_ORIGINS):
    if not o:
        continue
    o = o.strip()
    if o and o not in seen:
        seen.add(o)
        merged.append(o)

# ⚠️ If someone configured "*" in settings, you cannot use credentials with it
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
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {type(exc).__name__}: {exc}"},
    )

app.include_router(api_router)

@app.get("/health")
def health():
    return {"ok": True}
