from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.api.deps import require_staff

router = APIRouter(prefix="/case-notes", tags=["case-notes"])


class CaseNoteCreateIn(BaseModel):
    entity_type: str  # "complaint" | "officer"
    entity_id: int
    note_text: str
    note_type: str | None = None
    note_date: date | None = None


@router.get("", dependencies=[Depends(require_staff)])
def list_case_notes(
    entity_type: str = Query(...),
    entity_id: int = Query(...),
    db: Session = Depends(get_db),
):
    if entity_type not in ("complaint", "officer"):
        raise HTTPException(status_code=400, detail="entity_type must be 'complaint' or 'officer'")

    rows = (
        db.query(models.CaseNote)
        .filter(models.CaseNote.entity_type == entity_type, models.CaseNote.entity_id == entity_id)
        .order_by(models.CaseNote.created_at.desc())
        .limit(200)
        .all()
    )

    return [
        {
            "id": r.id,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "note_text": r.note_text,
            "note_type": r.note_type,
            "note_date": r.note_date,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("", dependencies=[Depends(require_staff)])
def create_case_note(payload: CaseNoteCreateIn, db: Session = Depends(get_db)):
    if payload.entity_type not in ("complaint", "officer"):
        raise HTTPException(status_code=400, detail="entity_type must be 'complaint' or 'officer'")

    row = models.CaseNote(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        note_text=payload.note_text,
        note_type=payload.note_type,
        note_date=payload.note_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "id": row.id,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "note_text": row.note_text,
        "note_type": row.note_type,
        "note_date": row.note_date,
        "created_at": row.created_at,
    }
