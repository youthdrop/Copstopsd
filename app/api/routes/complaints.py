from __future__ import annotations

import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_staff, require_admin
from app.db.models import Complaint, ComplaintFollowUp, Officer
from app.db.session import get_db
from app.schemas import ComplaintCreate, ComplaintOut, ComplaintUpdate

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


def normalize_harm_types(
    harm_types: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    harm_done: Optional[str] = None,
) -> List[str]:
    raw: List[str] = []
    if harm_types:
        raw = harm_types
    elif types:
        raw = types
    elif harm_done:
        raw = [x.strip() for x in harm_done.split(",") if x.strip()]

    # de-dupe, preserve order
    out: List[str] = []
    seen = set()
    for x in raw:
        s = str(x).strip()
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


def set_officers_from_ids(db: Session, complaint: Complaint, officer_ids: Optional[List[int]]):
    if officer_ids is None:
        return
    complaint.officers.clear()
    if not officer_ids:
        return
    officers = db.query(Officer).filter(Officer.id.in_(officer_ids)).all()
    for o in officers:
        complaint.officers.append(o)


@router.post("/complaints", response_model=ComplaintOut, dependencies=[Depends(require_staff)])
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    stop_time_obj = parse_hhmm(payload.stop_time)
    harms = normalize_harm_types(payload.harm_types, payload.types, payload.harm_done)

    complaint = Complaint(
        case_number=generate_case_number(),
        source="web",
        status="open",
        complainant_first_name=payload.complainant_first_name,
        complainant_last_name=payload.complainant_last_name,
        complainant_email=str(payload.complainant_email) if payload.complainant_email else None,
        complainant_phone=payload.complainant_phone,
        stop_date=payload.stop_date,
        stop_time=stop_time_obj,
        department=payload.department,
        unit=payload.unit,
        stop_location=payload.stop_location,
        narrative=payload.narrative,
        harm_types=harms,
        harm_done=", ".join(harms) if harms else (payload.harm_done or None),
    )

    db.add(complaint)
    db.flush()

    if payload.officer_ids:
        set_officers_from_ids(db, complaint, payload.officer_ids)

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


@router.patch("/complaints/{complaint_id}", response_model=ComplaintOut, dependencies=[Depends(require_staff)])
def update_complaint(complaint_id: int, payload: ComplaintUpdate, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if payload.complainant_first_name is not None:
        complaint.complainant_first_name = payload.complainant_first_name
    if payload.complainant_last_name is not None:
        complaint.complainant_last_name = payload.complainant_last_name
    if payload.complainant_email is not None:
        complaint.complainant_email = str(payload.complainant_email)
    if payload.complainant_phone is not None:
        complaint.complainant_phone = payload.complainant_phone

    if payload.stop_date is not None:
        complaint.stop_date = payload.stop_date
    if payload.stop_time is not None:
        complaint.stop_time = parse_hhmm(payload.stop_time)

    if payload.department is not None:
        complaint.department = payload.department
    if payload.unit is not None:
        complaint.unit = payload.unit
    if payload.stop_location is not None:
        complaint.stop_location = payload.stop_location

    if payload.status is not None:
        complaint.status = payload.status

    if payload.narrative is not None:
        complaint.narrative = payload.narrative

    # harms
    if payload.harm_types is not None or payload.types is not None or payload.harm_done is not None:
        harms = normalize_harm_types(payload.harm_types, payload.types, payload.harm_done)
        complaint.harm_types = harms
        complaint.harm_done = ", ".join(harms) if harms else None

    # officers attach later
    if payload.officer_ids is not None:
        set_officers_from_ids(db, complaint, payload.officer_ids)

    db.commit()
    db.refresh(complaint)
    return complaint


@router.delete("/complaints/{complaint_id}", dependencies=[Depends(require_admin)])
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

# -------------------------
# Complaint follow-up
# -------------------------
ALLOWED_FINDINGS = {"Miscellaneous", "Sustained", "Not Sustained", "Exonerated", "Unfounded"}


class FollowUpUpdate(BaseModel):
    original_submitted_date: Optional[str] = None
    original_submitted_to: Optional[List[str]] = None
    original_case_note: Optional[str] = None
    ia_case_number: Optional[str] = None
    ia_status: Optional[str] = None
    ia_case_note: Optional[str] = None
    cpp_case_number: Optional[str] = None
    cpp_status: Optional[str] = None
    cpp_case_note: Optional[str] = None
    disposition_date: Optional[str] = None
    disposition_findings: Optional[List[str]] = None
    disposition_case_note: Optional[str] = None


def _date_or_none(value: Optional[str]):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {value}")


def _followup_to_dict(row: ComplaintFollowUp) -> dict:
    return {
        "id": row.id,
        "complaint_id": row.complaint_id,
        "original_submitted_date": row.original_submitted_date.isoformat() if row.original_submitted_date else None,
        "original_submitted_to": row.original_submitted_to or [],
        "original_case_note": row.original_case_note,
        "ia_case_number": row.ia_case_number,
        "ia_status": row.ia_status,
        "ia_case_note": row.ia_case_note,
        "cpp_case_number": row.cpp_case_number,
        "cpp_status": row.cpp_status,
        "cpp_case_note": row.cpp_case_note,
        "disposition_date": row.disposition_date.isoformat() if row.disposition_date else None,
        "disposition_findings": row.disposition_findings or ["Miscellaneous"],
        "disposition_case_note": row.disposition_case_note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _get_complaint_or_404(db: Session, complaint_id: int):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.get("/complaints/{complaint_id}/follow-up", dependencies=[Depends(require_staff)])
def get_follow_up(complaint_id: int, db: Session = Depends(get_db)):
    _get_complaint_or_404(db, complaint_id)
    row = db.query(ComplaintFollowUp).filter(ComplaintFollowUp.complaint_id == complaint_id).first()
    if not row:
        row = ComplaintFollowUp(complaint_id=complaint_id, disposition_findings=["Miscellaneous"])
        db.add(row)
        db.commit()
        db.refresh(row)
    return _followup_to_dict(row)


@router.patch("/complaints/{complaint_id}/follow-up", dependencies=[Depends(require_staff)])
def update_follow_up(complaint_id: int, payload: FollowUpUpdate, db: Session = Depends(get_db)):
    _get_complaint_or_404(db, complaint_id)
    row = db.query(ComplaintFollowUp).filter(ComplaintFollowUp.complaint_id == complaint_id).first()
    if not row:
        row = ComplaintFollowUp(complaint_id=complaint_id, disposition_findings=["Miscellaneous"])
        db.add(row)

    data = payload.model_dump(exclude_unset=True)

    if "original_submitted_date" in data:
        row.original_submitted_date = _date_or_none(data.pop("original_submitted_date"))
    if "disposition_date" in data:
        row.disposition_date = _date_or_none(data.pop("disposition_date"))
    if "disposition_findings" in data:
        findings = data.pop("disposition_findings") or ["Miscellaneous"]
        invalid = [value for value in findings if value not in ALLOWED_FINDINGS]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid disposition finding: {invalid[0]}")
        row.disposition_findings = findings

    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return _followup_to_dict(row)

