from __future__ import annotations

import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_staff
from app.db.models import Complaint, Officer
from app.db.session import get_db
from app.schemas import ComplaintCreate, ComplaintOut

router = APIRouter()


def generate_case_number() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    rand = secrets.token_hex(2).upper()
    return f"PA-{stamp}-{rand}"


def parse_hhmm(value: Optional[str]):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except Exception:
        return None


@router.post("/complaints", response_model=ComplaintOut, dependencies=[Depends(require_staff)])
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    stop_time_obj = parse_hhmm(payload.stop_time)

    complaint = Complaint(
        case_number=generate_case_number(),
        source="web",
        status="open",
        complainant_first_name=payload.complainant_first_name,
        complainant_last_name=payload.complainant_last_name,
        complainant_email=payload.complainant_email,
        complainant_phone=payload.complainant_phone,
        stop_date=payload.stop_date,
        stop_time=stop_time_obj,  # ✅ saves time
        department=payload.department,
        unit=payload.unit,
        stop_location=payload.stop_location,
        narrative=payload.narrative,
    )

    db.add(complaint)
    db.flush()

    if payload.officer_ids:
        officers = db.query(Officer).filter(Officer.id.in_(payload.officer_ids)).all()
        for officer in officers:
            complaint.officers.append(officer)

    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/complaints", response_model=List[ComplaintOut], dependencies=[Depends(require_staff)])
def list_complaints(db: Session = Depends(get_db)):
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()


@router.get("/complaints/{complaint_id}", response_model=ComplaintOut, dependencies=[Depends(require_staff)])
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.delete("/complaints/{complaint_id}", dependencies=[Depends(require_staff)])
def delete_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    try:
        complaint.officers.clear()
    except Exception:
        pass

    db.delete(complaint)
    db.commit()
    return {"ok": True, "deleted_id": complaint_id}
