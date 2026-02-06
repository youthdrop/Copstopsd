from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User   # ✅ FIXED
from app.utils import (
    generate_otp,
    hash_otp,
    verify_otp,
    hash_password,
    reset_otp_expires_at,
    send_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])



@router.post("/forgot-password")
def forgot_password(payload: dict, db: Session = Depends(get_db)):
    """
    Always returns {"ok": True} to avoid leaking whether a user exists.
    If SMTP isn't configured, you can still DEV-print the code.
    """
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return {"ok": True}

    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"ok": True}

    code = generate_otp()
    user.reset_otp_hash = hash_otp(code)
    user.reset_otp_expires_at = reset_otp_expires_at()
    db.commit()

    # DEV shortcut so you can test even if SMTP isn’t configured yet
    print(f"[DEV RESET OTP] {email} -> {code}")

    # Try email (if SMTP configured)
    try:
        send_email(
            to_email=email,
            subject="Password reset code",
            body=f"Your 6-digit password reset code is: {code}\n\nIt expires in 10 minutes."
        )
    except Exception:
        # Don’t fail the request if email isn’t configured yet
        pass

    return {"ok": True}


@router.post("/reset-password")
def reset_password(payload: dict, db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    code = (payload.get("code") or "").strip()
    new_password = payload.get("new_password") or ""

    if not email or not code or not new_password:
        return {"ok": False, "detail": "Missing email, code, or new_password"}

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.reset_otp_hash or not user.reset_otp_expires_at:
        return {"ok": False, "detail": "Invalid code"}

    if user.reset_otp_expires_at < datetime.utcnow():
        return {"ok": False, "detail": "Code expired"}

    if not verify_otp(code, user.reset_otp_hash):
        return {"ok": False, "detail": "Invalid code"}

    user.password_hash = hash_password(new_password)
    user.reset_otp_hash = None
    user.reset_otp_expires_at = None
    db.commit()

    return {"ok": True}
