# backend/app/utils.py

from datetime import datetime, timedelta
import os
import random
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext


# =========================
# PASSWORD HASHING (ARGON2)
# =========================
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

# Optional sanity limit (Argon2 does NOT require this, but prevents abuse)
MAX_PASSWORD_CHARS = 256


def utcnow():
    return datetime.utcnow()


def generate_case_number(prefix: str = "PA") -> str:
    """
    Example: PA-20260124-1530
    Prefix + YYYYMMDD + random 4 digits.
    """
    date_part = utcnow().strftime("%Y%m%d")
    rand_part = f"{random.randint(0, 9999):04d}"
    return f"{prefix}-{date_part}-{rand_part}"


def hash_password(password: str) -> str:
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    if len(password) > MAX_PASSWORD_CHARS:
        raise HTTPException(status_code=400, detail="Password too long")
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not password:
        return False
    if len(password) > MAX_PASSWORD_CHARS:
        return False
    return pwd_context.verify(password, password_hash)


# =========================
# JWT / OTP HELPERS
# =========================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
RESET_OTP_EXPIRE_MINUTES = int(os.getenv("RESET_OTP_EXPIRE_MINUTES", "10"))


def create_access_token(user_id: int) -> str:
    expire = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def hash_otp(code: str) -> str:
    return pwd_context.hash(code)


def verify_otp(code: str, code_hash: str) -> bool:
    return pwd_context.verify(code, code_hash)


# =========================
# EMAIL (SMTP)
# =========================
def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Uses SMTP settings from env:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL
    If SMTP isn't configured, raises 500.
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pw = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL") or user

    if not host or not user or not pw or not from_email:
        raise HTTPException(status_code=500, detail="SMTP is not configured (missing SMTP_* env vars).")

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pw)
        s.send_message(msg)


def reset_otp_expires_at() -> datetime:
    return utcnow() + timedelta(minutes=RESET_OTP_EXPIRE_MINUTES)
