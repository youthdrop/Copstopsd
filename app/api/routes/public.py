from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.schemas import ComplaintPublicCreate
from app.utils import generate_case_number

try:
    from app.services.email import send_new_submission_email  # type: ignore
except Exception:
    send_new_submission_email = None  # type: ignore

router = APIRouter(prefix="/public", tags=["public"])


def parse_hhmm(value: Optional[str]):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except Exception:
        return None


def normalize_harm_done(value: Any) -> Optional[str]:
    """
    Legacy storage helper: some older clients send harm_done as a list.
    This converts list -> JSON string. We keep this for backward compatibility,
    but the canonical storage is complaints.harm_types (TEXT[]).
    """
    if value is None:
        return None
    if isinstance(value, list):
        cleaned = [str(x).strip() for x in value if str(x).strip()]
        return json.dumps(cleaned) if cleaned else None
    s = str(value).strip()
    return s or None


def normalize_harm_types(value: Any) -> List[str]:
    """
    Canonical harms list for complaints.harm_types (TEXT[]).

    Accepts:
      - list[str]
      - JSON string like '["A","B"]'
      - comma-separated string 'A, B'
      - None
    """
    if value is None:
        return []

    # list input
    if isinstance(value, list):
        out: List[str] = []
        seen = set()
        for x in value:
            s = str(x).strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(s)
        return out

    s = str(value).strip()
    if not s:
        return []

    # JSON array string input
    if s.startswith("["):
        try:
            arr = json.loads(s)
            if isinstance(arr, list):
                return normalize_harm_types(arr)
        except Exception:
            pass

    # comma-separated fallback
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return normalize_harm_types(parts)


def harms_to_readable(harms: List[str]) -> Optional[str]:
    return ", ".join(harms) if harms else None


@router.post("/complaints")
def submit_public_complaint(payload: ComplaintPublicCreate, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    parts = name.split()
    first = parts[0] if parts else "Unknown"
    last = " ".join(parts[1:]) if len(parts) > 1 else "Unknown"

    # Public web form might send harm_types or harm_done. Prefer harm_types.
    harms = normalize_harm_types(getattr(payload, "harm_types", None) or getattr(payload, "harm_done", None))

    complaint = models.Complaint(
        case_number=generate_case_number(),
        source="public",
        complainant_first_name=first,
        complainant_last_name=last,
        complainant_email=payload.email,
        complainant_phone=(payload.complainant_phone or "").strip() or None,
        stop_date=payload.stop_date,
        stop_time=parse_hhmm(payload.stop_time),
        department=payload.department,
        unit=payload.unit,
        stop_location=payload.stop_location,
        narrative=payload.narrative,
        status="open",
        harm_types=harms,
        harm_done=harms_to_readable(harms) or normalize_harm_done(getattr(payload, "harm_done", None)),
    )

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


# -------------------------
# MOBILE INTAKE (public)
# -------------------------
class ComplaintMobileIntake(BaseModel):
    complainant_first_name: str
    complainant_last_name: str
    complainant_phone: Optional[str] = None

    department: str
    stop_date: date
    stop_time: Optional[str] = None  # "HH:MM"

    # Mobile multi-select harms (list)
    harm_done: Optional[List[str]] = None


@router.post("/intake")
def submit_mobile_intake(payload: ComplaintMobileIntake, db: Session = Depends(get_db)):
    harms = normalize_harm_types(payload.harm_done)

    complaint = models.Complaint(
        case_number=generate_case_number(),
        source="mobile_public",
        complainant_first_name=payload.complainant_first_name.strip(),
        complainant_last_name=payload.complainant_last_name.strip(),
        complainant_phone=(payload.complainant_phone or "").strip() or None,
        stop_date=payload.stop_date,
        stop_time=parse_hhmm(payload.stop_time),
        department=(payload.department or "").strip(),
        narrative=None,
        status="open",
        # ✅ key fix
        harm_types=harms,
        harm_done=harms_to_readable(harms),
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    if send_new_submission_email:
        try:
            send_new_submission_email(
                case_number=complaint.case_number,
                summary="New mobile complaint",
                link=f"/complaints/{complaint.id}",
            )
        except Exception:
            pass

    return {"ok": True, "case_number": complaint.case_number, "complaint_id": complaint.id}

