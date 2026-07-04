from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User


def _user_id_from_dev_token(token: str) -> int | None:
    prefix = "dev-token-"
    if not token.startswith(prefix):
        return None
    try:
        return int(token.replace(prefix, "", 1))
    except ValueError:
        return None


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    user_id = _user_id_from_dev_token(parts[1])
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not bool(getattr(user, "is_active", True)):
        raise HTTPException(status_code=403, detail="Account disabled")

    return user


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    # Any active authenticated user is staff-level or higher.
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not bool(getattr(current_user, "is_admin", False)):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": getattr(user, "full_name", None),
        "is_active": bool(getattr(user, "is_active", True)),
        "is_admin": bool(getattr(user, "is_admin", False)),
        "is_verified": bool(getattr(user, "is_verified", False)),
        "created_at": getattr(user, "created_at", None),
        "updated_at": getattr(user, "updated_at", None),
    }
