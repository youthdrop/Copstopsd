from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.schemas import ComplaintPublicCreate
from app.utils import generate_case_number

# Email sending might not be configured in production; don't let it break intake
try:
    from app.services.email import send_new_submission_email  # type: ignore
except Exception:
    send_new_submission_email = None  # type: ignore

router = APIRouter(prefix="/public", tags=["public"])


# -------------------------
# Existing WEB public intake
# -------------------------
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

    from datetime import date
from pydantic import BaseModel


class ComplaintMobileIntake(BaseModel):
    complainant_first_name: str
    complainant_last_name: str
    complainant_phone: str
    stop_date: date
    narrative: str


@router.post("/intake")
def submit_mobile_intake(
    payload: ComplaintMobileIntake,
    db: Session = Depends(get_db),
):
    complaint = models.Complaint(
        case_number=generate_case_number(),
        source="mobile_public",
        complainant_first_name=payload.complainant_first_name.strip(),
        complainant_last_name=payload.complainant_last_name.strip(),
        stop_date=payload.stop_date,
        narrative=payload.narrative.strip(),
        status="open",
    )

    phone = payload.complainant_phone.strip()
    if phone:
        if hasattr(models.Complaint, "complainant_phone"):
            setattr(complaint, "complainant_phone", phone)
        else:
            complaint.narrative = f"PHONE: {phone}\n\n{complaint.narrative}"

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {
        "ok": True,
        "case_number": complaint.case_number,
        "complaint_id": complaint.id,
    }

class ComplaintMobileIntake(BaseModel):
    complainant_first_name: str
    complainant_last_name: str
    complainant_phone: str
    stop_date: date
    narrative: str


@router.post("/intake")
def submit_mobile_intake(
    payload: ComplaintMobileIntake,
    db: Session = Depends(get_db),
):
    complaint = models.Complaint(
        case_number=generate_case_number(),
        source="mobile_public",
        complainant_first_name=payload.complainant_first_name.strip(),
        complainant_last_name=payload.complainant_last_name.strip(),
        stop_date=payload.stop_date,
        narrative=(payload.narrative or "").strip(),
        status="open",
    )

    phone = (payload.complainant_phone or "").strip()
    if phone:
        # Save to column if it exists; otherwise prepend to narrative
        if hasattr(models.Complaint, "complainant_phone"):
            try:
                setattr(complaint, "complainant_phone", phone)
            except Exception:
                complaint.narrative = f"PHONE: {phone}\n\n{complaint.narrative}"
        else:
            complaint.narrative = f"PHONE: {phone}\n\n{complaint.narrative}"

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    if send_new_submission_email:
        try:
            send_new_submission_email(
                case_number=complaint.case_number,
                summary=(complaint.narrative or "")[:500],
                link=f"/complaints/{complaint.id}",
            )
        except Exception:
            pass

    return {"ok": True, "case_number": complaint.case_number, "complaint_id": complaint.id}

    # Optional officer linking
    if getattr(payload, "officer_ids", None):
        officers = (
            db.query(models.Officer)
            .filter(models.Officer.id.in_(payload.officer_ids))
            .all()
        )
        complaint.officers = officers

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Notify staff (best-effort)
    if send_new_submission_email:
        try:
            send_new_submission_email(
                case_number=complaint.case_number,
                summary=(complaint.narrative or "")[:500],
                link=f"/complaints/{complaint.id}",
            )
        except Exception:
            pass

    return {
        "ok": True,
        "case_number": complaint.case_number,
        "complaint_id": complaint.id,
    }


# -------------------------
# NEW MOBILE public intake (minimal fields)
# -------------------------
class ComplaintMobileIntake(BaseModel):
    complainant_first_name: str
    complainant_last_name: str
    complainant_phone: str
    stop_date: date
    narrative: str


@router.post("/intake")
def submit_mobile_intake(
    payload: ComplaintMobileIntake,
    db: Session = Depends(get_db),
):
    # Create complaint with minimal fields
    complaint = models.Complaint(
        case_number=generate_case_number(),
        source="mobile_public",
        complainant_first_name=payload.complainant_first_name.strip(),
        complainant_last_name=payload.complainant_last_name.strip(),
        stop_date=payload.stop_date,
        narrative=payload.narrative.strip(),
        status="open",
    )

    # Phone handling:
    # If your DB model has complainant_phone, save it there.
    # If not, we prepend it to narrative so we never crash on missing column.
    phone = (payload.complainant_phone or "").strip()
    if phone:
        if hasattr(models.Complaint, "complainant_phone"):
            try:
                setattr(complaint, "complainant_phone", phone)
            except Exception:
                # fallback if mapping differs
                complaint.narrative = f"PHONE: {phone}\n\n{complaint.narrative}"
        else:
            complaint.narrative = f"PHONE: {phone}\n\n{complaint.narrative}"

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Notify staff (best-effort)
    if send_new_submission_email:
        try:
            send_new_submission_email(
                case_number=complaint.case_number,
                summary=(complaint.narrative or "")[:500],
                link=f"/complaints/{complaint.id}",
            )
        except Exception:
            pass

    return {
        "ok": True,
        "case_number": complaint.case_number,
        "complaint_id": complaint.id,
    }
