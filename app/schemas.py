from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional, Any

from pydantic import BaseModel, EmailStr, Field, field_serializer


# ---------------------------------
# Officers
# ---------------------------------
class OfficerCreate(BaseModel):
    first_name: str
    last_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = None


class OfficerOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------
# Complaints
# ---------------------------------
class ComplaintCreate(BaseModel):
    complainant_first_name: str
    complainant_last_name: str
    complainant_email: Optional[EmailStr] = None
    complainant_phone: Optional[str] = None

    stop_date: date
    stop_time: Optional[str] = None  # accepts "HH:MM"

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    # ✅ harms (canonical)
    harm_types: List[str] = Field(default_factory=list)

    # ✅ backward-compat (some clients might still send these)
    types: Optional[List[str]] = None
    harm_done: Optional[str] = None

    narrative: Optional[str] = None
    officer_ids: Optional[List[int]] = None


class ComplaintUpdate(BaseModel):
    # all optional because it's a PATCH
    complainant_first_name: Optional[str] = None
    complainant_last_name: Optional[str] = None
    complainant_email: Optional[EmailStr] = None
    complainant_phone: Optional[str] = None

    stop_date: Optional[date] = None
    stop_time: Optional[str] = None

    department: Optional[str] = None
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    status: Optional[str] = None
    narrative: Optional[str] = None

    # ✅ canonical harms update
    harm_types: Optional[List[str]] = None

    # backward-compat
    types: Optional[List[str]] = None
    harm_done: Optional[str] = None

    # to attach/change officers later
    officer_ids: Optional[List[int]] = None


class ComplaintOut(BaseModel):
    id: int
    case_number: str
    source: Optional[str] = None

    complainant_first_name: str
    complainant_last_name: str
    complainant_email: Optional[EmailStr] = None
    complainant_phone: Optional[str] = None

    stop_date: date
    stop_time: Optional[time] = None

    @field_serializer("stop_time")
    def _serialize_stop_time(self, v: Optional[time], _info: Any) -> Optional[str]:
        return v.strftime("%H:%M") if v else None

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    # ✅ canonical harms returned to web/mobile
    harm_types: List[str] = Field(default_factory=list)

    # legacy (kept so old UI doesn't break)
    harm_done: Optional[str] = None

    narrative: Optional[str] = None
    status: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    officers: List[OfficerOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ---------------------------------
# Case Notes
# ---------------------------------
class CaseNoteCreate(BaseModel):
    entity_type: str  # "complaint" | "officer"
    entity_id: int
    note_text: str
    note_type: Optional[str] = None
    note_date: Optional[date] = None


class CaseNoteOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    note_text: str
    note_type: Optional[str] = None
    note_date: Optional[date] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
