from __future__ import annotations

from datetime import datetime, timedelta
import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.db.session import get_db
from app.db.models import User

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
        otp_hash=None,
        otp_expires_at=None,
        created_at=datetime.utcnow(),
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

    # ✅ OTP creation (THIS is what you were missing)
    otp = generate_otp()
    user.otp_hash = ph.hash(otp)
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    db.commit()

    send_otp(user.email, otp)

    return {"ok": True, "email": user.email}


@router.post("/verify-otp", response_model=VerifyOtpOut)
def verify_otp(payload: VerifyOtpIn, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="OTP not requested")

    if not user.otp_hash or not user.otp_expires_at:
        raise HTTPException(status_code=401, detail="OTP not requested")

    if datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=401, detail="OTP expired")

    try:
        ok = ph.verify(user.otp_hash, payload.otp_code)
    except VerifyMismatchError:
        ok = False

    if not ok:
        raise HTTPException(status_code=401, detail="Invalid code")

    # Clear OTP after success
    user.otp_hash = None
    user.otp_expires_at = None
    user.is_verified = True
    db.commit()

    return {"ok": True, "access_token": make_access_token(user.id)}
