from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.schemas import ComplaintPublicCreate
from app.utils import generate_case_number
from app.services.email import send_new_submission_email

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/complaints")
def submit_public_complaint(
    payload: ComplaintPublicCreate,
    db: Session = Depends(get_db),
):
    # Best-effort name parsing
    name = (payload.name or "").strip()
    parts = name.split()
    first = parts[0] if parts else "Unknown"
    last = " ".join(parts[1:]) if len(parts) > 1 else "Unknown"

    complaint = models.Complaint(
        case_number=generate_case_number(),
        source="public",
        complainant_first_name=first,
        complainant_last_name=last,
        complainant_email=payload.email,
        stop_date=payload.stop_date,
        department=payload.department,
        unit=payload.unit,
        stop_location=payload.stop_location,
        narrative=payload.narrative,
        status="open",
    )

    # Optional officer linking
    if payload.officer_ids:
        officers = (
            db.query(models.Officer)
            .filter(models.Officer.id.in_(payload.officer_ids))
            .all()
        )
        complaint.officers = officers

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Notify staff
    send_new_submission_email(
        case_number=complaint.case_number,
        summary=complaint.narrative[:500],
        link=f"/complaints/{complaint.id}",
    )

    return {
        "ok": True,
        "case_number": complaint.case_number,
        "complaint_id": complaint.id,
    }
