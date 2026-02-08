from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.db.session import get_db
from app.db.models import User
import os

print("DEPLOY_SHA", os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("GIT_COMMIT_SHA") or "unknown")


# Optional: if you later wire up SMTP in app/services/email.py
try:
    from app.services.email import send_otp_email  # type: ignore
except Exception:
    send_otp_email = None


router = APIRouter(prefix="/auth", tags=["auth"])

ph = PasswordHasher()
OTP_EXPIRE_MINUTES = 10


# -------------------------
# Schemas
# -------------------------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    ok: bool
    email: EmailStr


class VerifyOtpIn(BaseModel):
    email: EmailStr
    otp_code: str  # "123456"


class VerifyOtpOut(BaseModel):
    ok: bool
    access_token: str


# -------------------------
# Helpers
# -------------------------
def normalize_email(email: str) -> str:
    return email.strip().lower()


def utcnow() -> datetime:
    """Timezone-aware UTC now (fixes naive/aware comparison bugs)."""
    return datetime.now(timezone.utc)


def ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Normalize datetimes from DB. If a naive datetime sneaks in, assume it is UTC.
    This prevents: TypeError: can't compare offset-naive and offset-aware datetimes
    """
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(password) > 256:
        raise HTTPException(status_code=400, detail="Password too long")
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def send_otp(email: str, code: str) -> None:
    """
    If SMTP/email is wired up, send a real email.
    Otherwise print to terminal as a dev fallback.
    """
    if send_otp_email:
        try:
            send_otp_email(email, code)
            return
        except Exception:
            pass

    print(f"[DEV OTP] {email} → {code}")


def make_access_token(user_id: int) -> str:
    # MVP token; replace with JWT later
    return f"dev-token-{user_id}"


def _clear_otp(user: User) -> None:
    user.otp_hash = None
    user.otp_expires_at = None
    user.otp_requested_at = None


# -------------------------
# Routes
# -------------------------
@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=(payload.full_name or "").strip() or None,
        is_active=True,
        is_verified=False,
        # created_at is server_default in model; setting it manually is optional
        # created_at=utcnow(),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"ok": True}


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create OTP (always timezone-aware UTC)
    otp = generate_otp()
    user.otp_hash = ph.hash(otp)
    user.otp_expires_at = utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    user.otp_requested_at = utcnow()
    db.commit()

    send_otp(user.email, otp)

    return {"ok": True, "email": user.email}


@router.post("/verify-otp", response_model=VerifyOtpOut)
def verify_otp(payload: VerifyOtpIn, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.otp_hash or not user.otp_expires_at:
        # Avoid leaking whether the user exists
        raise HTTPException(status_code=401, detail="OTP not requested")

    # Defensive: DB may return naive dt even if you intended timezone-aware
    expires_at = ensure_aware_utc(user.otp_expires_at)
    if not expires_at:
        raise HTTPException(status_code=401, detail="OTP not requested")

    now = utcnow()
    if now > expires_at:
        # Clear stale OTP so user can request again cleanly
        _clear_otp(user)
        db.commit()
        raise HTTPException(status_code=401, detail="OTP expired")

    try:
        ok = ph.verify(user.otp_hash, payload.otp_code)
    except VerifyMismatchError:
        ok = False
    except Exception:
        ok = False

    if not ok:
        raise HTTPException(status_code=401, detail="Invalid code")

    # Success: clear OTP and mark verified
    _clear_otp(user)
    user.is_verified = True
    db.commit()

    return {"ok": True, "access_token": make_access_token(user.id)}
