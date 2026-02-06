from __future__ import annotations

import os
import secrets
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Complaint, Officer
from app.schemas import ComplaintCreate, ComplaintOut

router = APIRouter()


def generate_case_number() -> str:
    """
    Generates a unique-ish case number without needing DB defaults.
    Example: PA-20260205-222348-A1B2
    """
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    rand = secrets.token_hex(2).upper()  # 4 hex chars
    return f"PA-{stamp}-{rand}"


def require_staff_key(x_staff_key: str | None) -> None:
    expected = os.getenv("STAFF_KEY", "dev-staff-key")
    if not x_staff_key:
        raise HTTPException(status_code=401, detail="Missing staff key")
    if x_staff_key != expected:
        raise HTTPException(status_code=403, detail="Invalid staff key")


# ----------------------------------------
# CREATE COMPLAINT (staff / authenticated)
# ----------------------------------------
@router.post("/complaints", response_model=ComplaintOut)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    x_staff_key: str = Header(default=None),
):
    require_staff_key(x_staff_key)

    complaint = Complaint(
        # ✅ MUST NOT be null in DB
        case_number=generate_case_number(),
        source="web",
        status="open",
        complainant_first_name=payload.complainant_first_name,
        complainant_last_name=payload.complainant_last_name,
        complainant_email=payload.complainant_email,
        # ✅ CORRECT FIELD NAME
        complainant_phone=payload.complainant_phone,
        stop_date=payload.stop_date,
        department=payload.department,
        unit=payload.unit,
        stop_location=payload.stop_location,
        narrative=payload.narrative,
    )

    db.add(complaint)
    db.flush()  # assigns complaint.id

    # ----------------------------------------
    # Optional officer linking
    # ----------------------------------------
    if payload.officer_ids:
        officers = (
            db.query(Officer)
            .filter(Officer.id.in_(payload.officer_ids))
            .all()
        )
        # If you want to enforce all officer_ids exist, uncomment:
        # if len(officers) != len(set(payload.officer_ids)):
        #     raise HTTPException(status_code=400, detail="One or more officers not found")

        for officer in officers:
            complaint.officers.append(officer)

    db.commit()
    return complaint


# ----------------------------------------
# LIST COMPLAINTS
# ----------------------------------------
@router.get("/complaints", response_model=List[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    return (
        db.query(Complaint)
        .order_by(Complaint.created_at.desc())
        .all()
    )


# ----------------------------------------
# GET SINGLE COMPLAINT
# ----------------------------------------
@router.get("/complaints/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint
