from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.db import models
from app.api.deps import require_staff

router = APIRouter(prefix="/officers", tags=["officers"])


# -------------------------
# Schemas
# -------------------------
class OfficerCreateIn(BaseModel):
    first_name: str
    last_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = None
    unit: Optional[str] = None


class OfficerUpdateIn(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    badge_number: Optional[str] = None
    department: Optional[str] = None
    unit: Optional[str] = None


def officer_to_dict(o: models.Officer) -> dict:
    return {
        "id": o.id,
        "first_name": o.first_name,
        "last_name": o.last_name,
        "badge_number": o.badge_number,
        "department": o.department,
        "unit": o.unit,
    }


# -------------------------
# Routes
# -------------------------
@router.get("", dependencies=[Depends(require_staff)])
def list_officers(
    q: str = Query("", description="Search by name, badge, department, unit"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Officer)

    q_clean = (q or "").strip()
    if q_clean:
        like = f"%{q_clean}%"
        query = query.filter(
            or_(
                models.Officer.first_name.ilike(like),
                models.Officer.last_name.ilike(like),
                models.Officer.badge_number.ilike(like),
                models.Officer.department.ilike(like),
                models.Officer.unit.ilike(like),
            )
        )

    rows = query.order_by(models.Officer.last_name.asc(), models.Officer.first_name.asc()).limit(500).all()
    return [officer_to_dict(o) for o in rows]


@router.post("", dependencies=[Depends(require_staff)])
def create_officer(payload: OfficerCreateIn, db: Session = Depends(get_db)):
    first = (payload.first_name or "").strip()
    last = (payload.last_name or "").strip()
    if not first or not last:
        raise HTTPException(status_code=400, detail="first_name and last_name are required")

    o = models.Officer(
        first_name=first,
        last_name=last,
        badge_number=(payload.badge_number or "").strip() or None,
        department=(payload.department or "").strip() or None,
        unit=(payload.unit or "").strip() or None,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return officer_to_dict(o)


@router.get("/{officer_id}", dependencies=[Depends(require_staff)])
def get_officer(officer_id: int, db: Session = Depends(get_db)):
    o = db.query(models.Officer).filter(models.Officer.id == officer_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Officer not found")
    return officer_to_dict(o)


@router.patch("/{officer_id}", dependencies=[Depends(require_staff)])
def update_officer(officer_id: int, payload: OfficerUpdateIn, db: Session = Depends(get_db)):
    o = db.query(models.Officer).filter(models.Officer.id == officer_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Officer not found")

    if payload.first_name is not None:
        o.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        o.last_name = payload.last_name.strip()
    if payload.badge_number is not None:
        o.badge_number = payload.badge_number.strip() or None
    if payload.department is not None:
        o.department = payload.department.strip() or None
    if payload.unit is not None:
        o.unit = payload.unit.strip() or None

    if not o.first_name or not o.last_name:
        raise HTTPException(status_code=400, detail="first_name and last_name are required")

    db.commit()
    db.refresh(o)
    return officer_to_dict(o)


@router.delete("/{officer_id}", dependencies=[Depends(require_staff)])
def delete_officer(officer_id: int, db: Session = Depends(get_db)):
    o = db.query(models.Officer).filter(models.Officer.id == officer_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Officer not found")

    # SAFETY: prevent deleting an officer that is referenced by complaints.
    # If your join table model is named differently, change models.ComplaintOfficer below.
    if hasattr(models, "ComplaintOfficer"):
        link_exists = (
            db.query(models.ComplaintOfficer)
            .filter(models.ComplaintOfficer.officer_id == officer_id)
            .first()
            is not None
        )
        if link_exists:
            raise HTTPException(
                status_code=409,
                detail="Officer is linked to one or more complaints; unlink officer from complaints first.",
            )

    db.delete(o)
    db.commit()
    return {"ok": True, "deleted_id": officer_id}
