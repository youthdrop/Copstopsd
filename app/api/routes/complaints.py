from __future__ import annotations

import os
import secrets
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from fastapi.responses import Response
from sqlalchemy.orm import Session
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.api.deps import require_staff, require_admin
from app.db.models import Complaint, ComplaintDocument, ComplaintFollowUp, Officer
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


def _normalize_disposition_findings(values: Optional[List[Any]]) -> List[Dict[str, str]]:
    if not values:
        return [{"finding": "Miscellaneous", "description": ""}]

    normalized: List[Dict[str, str]] = []
    for value in values:
        if isinstance(value, str):
            finding = value.strip() or "Miscellaneous"
            description = ""
        elif isinstance(value, dict):
            finding = str(value.get("finding") or "Miscellaneous").strip()
            description = str(value.get("description") or "").strip()
        else:
            raise HTTPException(status_code=400, detail="Invalid disposition finding format")

        if finding not in ALLOWED_FINDINGS:
            raise HTTPException(status_code=400, detail=f"Invalid disposition finding: {finding}")

        normalized.append({"finding": finding, "description": description})

    return normalized


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
    disposition_findings: Optional[List[Any]] = None
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
        "disposition_findings": _normalize_disposition_findings(row.disposition_findings),
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
        row = ComplaintFollowUp(complaint_id=complaint_id, disposition_findings=[{"finding": "Miscellaneous", "description": ""}])
        db.add(row)
        db.commit()
        db.refresh(row)
    return _followup_to_dict(row)


@router.patch("/complaints/{complaint_id}/follow-up", dependencies=[Depends(require_staff)])
def update_follow_up(complaint_id: int, payload: FollowUpUpdate, db: Session = Depends(get_db)):
    _get_complaint_or_404(db, complaint_id)
    row = db.query(ComplaintFollowUp).filter(ComplaintFollowUp.complaint_id == complaint_id).first()
    if not row:
        row = ComplaintFollowUp(complaint_id=complaint_id, disposition_findings=[{"finding": "Miscellaneous", "description": ""}])
        db.add(row)

    data = payload.model_dump(exclude_unset=True)

    if "original_submitted_date" in data:
        row.original_submitted_date = _date_or_none(data.pop("original_submitted_date"))
    if "disposition_date" in data:
        row.disposition_date = _date_or_none(data.pop("disposition_date"))
    if "disposition_findings" in data:
        row.disposition_findings = _normalize_disposition_findings(
            data.pop("disposition_findings")
        )

    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return _followup_to_dict(row)

# -------------------------
# Complaint documents — Version 3 object storage
# -------------------------
DOCUMENT_SECTIONS = {
    "original_complaint",
    "internal_affairs",
    "cpp",
    "final_disposition",
}
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024 * 1024
PRESIGNED_UPLOAD_SECONDS = 15 * 60
PRESIGNED_DOWNLOAD_SECONDS = 15 * 60


class DocumentPresignIn(BaseModel):
    section: str
    original_filename: str
    content_type: Optional[str] = None
    file_size: int


def _bucket_setting(*names: str) -> str:
    for name in names:
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    raise RuntimeError(f"Missing object-storage variable: {' or '.join(names)}")


def _s3_settings() -> dict:
    return {
        "bucket": _bucket_setting("AWS_S3_BUCKET_NAME", "BUCKET"),
        "access_key": _bucket_setting("AWS_ACCESS_KEY_ID", "ACCESS_KEY_ID"),
        "secret_key": _bucket_setting("AWS_SECRET_ACCESS_KEY", "SECRET_ACCESS_KEY"),
        "region": _bucket_setting("AWS_DEFAULT_REGION", "REGION"),
        "endpoint": _bucket_setting("AWS_ENDPOINT_URL", "ENDPOINT"),
    }


def _s3_client():
    values = _s3_settings()
    return boto3.client(
        "s3",
        endpoint_url=values["endpoint"],
        aws_access_key_id=values["access_key"],
        aws_secret_access_key=values["secret_key"],
        region_name=values["region"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _document_to_dict(row: ComplaintDocument) -> dict:
    backend = row.storage_backend or ("database" if row.file_data else "bucket")
    return {
        "id": row.id,
        "complaint_id": row.complaint_id,
        "section": row.section,
        "original_filename": row.original_filename,
        "content_type": row.content_type,
        "file_size": row.file_size,
        "storage_key": row.storage_key,
        "storage_backend": backend,
        "upload_status": row.upload_status or ("uploaded" if row.file_data else "pending"),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _validate_document_section(section: str) -> str:
    value = (section or "").strip()
    if value not in DOCUMENT_SECTIONS:
        raise HTTPException(status_code=400, detail="Invalid document section")
    return value


def _safe_storage_filename(filename: str) -> str:
    cleaned = (filename or "document").replace("\\", "_").replace("/", "_")
    cleaned = cleaned.replace("\r", "").replace("\n", "").strip()
    return (cleaned or "document")[:240]


@router.get("/complaints/{complaint_id}/documents", dependencies=[Depends(require_staff)])
def list_complaint_documents(
    complaint_id: int,
    section: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    _get_complaint_or_404(db, complaint_id)
    query = db.query(ComplaintDocument).filter(
        ComplaintDocument.complaint_id == complaint_id
    )
    if section:
        query = query.filter(
            ComplaintDocument.section == _validate_document_section(section)
        )
    rows = query.order_by(ComplaintDocument.created_at.desc()).all()
    return [_document_to_dict(row) for row in rows]


@router.post("/complaints/{complaint_id}/documents/presign", dependencies=[Depends(require_staff)])
def create_document_upload_ticket(
    complaint_id: int,
    payload: DocumentPresignIn,
    db: Session = Depends(get_db),
):
    _get_complaint_or_404(db, complaint_id)
    section = _validate_document_section(payload.section)
    if payload.file_size <= 0:
        raise HTTPException(status_code=400, detail="File size must be greater than zero")
    if payload.file_size > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 5 GB limit")

    filename = _safe_storage_filename(payload.original_filename)
    content_type = (payload.content_type or "application/octet-stream").strip()
    object_key = (
        f"complaints/{complaint_id}/{section}/"
        f"{uuid.uuid4().hex}-{filename}"
    )

    row = ComplaintDocument(
        complaint_id=complaint_id,
        section=section,
        original_filename=filename,
        content_type=content_type,
        file_size=payload.file_size,
        storage_key=object_key,
        storage_backend="bucket",
        upload_status="pending",
        file_data=None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    values = _s3_settings()
    upload_url = _s3_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": values["bucket"],
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_UPLOAD_SECONDS,
        HttpMethod="PUT",
    )
    return {
        "document": _document_to_dict(row),
        "upload_url": upload_url,
        "upload_headers": {"Content-Type": content_type},
    }


@router.post("/complaint-documents/{document_id}/complete", dependencies=[Depends(require_staff)])
def complete_document_upload(document_id: int, db: Session = Depends(get_db)):
    row = db.query(ComplaintDocument).filter(
        ComplaintDocument.id == document_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    if not row.storage_key:
        raise HTTPException(status_code=400, detail="Document has no object-storage key")

    values = _s3_settings()
    try:
        result = _s3_client().head_object(
            Bucket=values["bucket"], Key=row.storage_key
        )
    except ClientError as exc:
        raise HTTPException(status_code=409, detail="Object upload is not complete") from exc

    actual_size = int(result.get("ContentLength") or 0)
    if actual_size <= 0:
        raise HTTPException(status_code=409, detail="Uploaded object is empty")

    row.file_size = actual_size
    row.upload_status = "uploaded"
    db.commit()
    db.refresh(row)
    return _document_to_dict(row)


@router.get("/complaint-documents/{document_id}/download-url", dependencies=[Depends(require_staff)])
def create_document_download_ticket(document_id: int, db: Session = Depends(get_db)):
    row = db.query(ComplaintDocument).filter(
        ComplaintDocument.id == document_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    if row.file_data and not row.storage_key:
        return {"download_url": f"/complaint-documents/{document_id}/legacy-download"}
    if not row.storage_key or row.upload_status != "uploaded":
        raise HTTPException(status_code=409, detail="Document upload is not complete")

    values = _s3_settings()
    safe_name = _safe_storage_filename(row.original_filename)
    url = _s3_client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": values["bucket"],
            "Key": row.storage_key,
            "ResponseContentDisposition": f'attachment; filename="{safe_name}"',
            "ResponseContentType": row.content_type or "application/octet-stream",
        },
        ExpiresIn=PRESIGNED_DOWNLOAD_SECONDS,
        HttpMethod="GET",
    )
    return {"download_url": url}


@router.get("/complaint-documents/{document_id}/legacy-download", dependencies=[Depends(require_staff)])
def download_legacy_document(document_id: int, db: Session = Depends(get_db)):
    row = db.query(ComplaintDocument).filter(
        ComplaintDocument.id == document_id
    ).first()
    if not row or not row.file_data:
        raise HTTPException(status_code=404, detail="Legacy document not found")

    safe_name = _safe_storage_filename(row.original_filename)
    return Response(
        content=row.file_data,
        media_type=row.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.delete("/complaint-documents/{document_id}", dependencies=[Depends(require_staff)])
def delete_complaint_document(document_id: int, db: Session = Depends(get_db)):
    row = db.query(ComplaintDocument).filter(
        ComplaintDocument.id == document_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    if row.storage_key:
        values = _s3_settings()
        try:
            _s3_client().delete_object(
                Bucket=values["bucket"], Key=row.storage_key
            )
        except ClientError as exc:
            raise HTTPException(
                status_code=502,
                detail="Could not delete object from storage",
            ) from exc

    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_id": document_id}
