from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session
from argon2 import PasswordHasher

from app.db.session import get_db
from app.db.models import User
from app.api.deps import require_admin, user_to_dict

router = APIRouter(prefix="/users", tags=["users"])
ph = PasswordHasher()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(password) > 256:
        raise HTTPException(status_code=400, detail="Password too long")
    return ph.hash(password)


class UserCreateIn(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    is_active: bool = True
    # New users are staff by default. Admin can promote later if truly needed.


class UserUpdateIn(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_verified: Optional[bool] = None


class PasswordResetIn(BaseModel):
    new_password: str


@router.get("")
def list_users(
    q: str = Query(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(User)
    search = q.strip()
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.email.ilike(like), User.full_name.ilike(like)))

    users = query.order_by(User.id.asc()).all()
    return [user_to_dict(u) for u in users]


@router.post("")
def create_user(
    payload: UserCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    email = normalize_email(payload.email)
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    now = utcnow()
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=(payload.full_name or "").strip() or None,
        is_active=payload.is_active,
        is_admin=False,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_dict(user)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None:
        email = normalize_email(payload.email)
        duplicate = db.query(User).filter(User.email == email, User.id != user_id).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = email

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or None

    if payload.is_active is not None:
        if user.id == current_user.id and payload.is_active is False:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        user.is_active = payload.is_active

    if payload.is_admin is not None:
        if user.id == current_user.id and payload.is_admin is False:
            raise HTTPException(status_code=400, detail="You cannot remove your own admin access while logged in")
        user.is_admin = payload.is_admin

    if payload.is_verified is not None:
        user.is_verified = payload.is_verified

    user.updated_at = utcnow()
    db.commit()
    db.refresh(user)
    return user_to_dict(user)


@router.patch("/{user_id}/password")
def reset_user_password(
    user_id: int,
    payload: PasswordResetIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    user.is_verified = True
    user.updated_at = utcnow()
    db.commit()
    return {"ok": True}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account while logged in")

    db.delete(user)
    db.commit()
    return {"ok": True, "deleted_id": user_id}
