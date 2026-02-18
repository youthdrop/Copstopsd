from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_serializer


# ---------------------------------
# Officers
# ---------------------------------
class OfficerCreate(BaseModel):
    first_name: str
    last_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = None
    unit: Optional[str] = None


class OfficerOut(OfficerCreate):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------
# Complaints (STAFF WEB)
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

    # ✅ NEW canonical harms list
    harm_types: List[str] = Field(default_factory=list)

    # backwards-compat (some clients might still send these)
    types: Optional[List[str]] = None
    harm_done: Optional[str] = None

    narrative: Optional[str] = None
    officer_ids: Optional[List[int]] = None


class ComplaintUpdate(BaseModel):
    # PATCH fields (all optional)
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

    harm_types: Optional[List[str]] = None
    types: Optional[List[str]] = None
    harm_done: Optional[str] = None

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

    # ✅ return canonical harms to web/mobile
    harm_types: List[str] = Field(default_factory=list)

    # legacy
    harm_done: Optional[str] = None

    narrative: Optional[str] = None
    status: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    officers: List[OfficerOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ---------------------------------
# Public intake (public web form)
# ---------------------------------
class ComplaintPublicCreate(BaseModel):
    name: str = Field(..., description="Complainant name (best-effort parsed into first/last)")
    email: Optional[EmailStr] = None
    complainant_phone: Optional[str] = None

    stop_date: date
    stop_time: Optional[str] = None

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    harm_types: List[str] = Field(default_factory=list)
    harm_done: Optional[str] = None

    narrative: Optional[str] = None
    officer_ids: Optional[List[int]] = None


# ---------------------------------
# Case Notes
# ---------------------------------
class CaseNoteCreate(BaseModel):
    entity_type: str
    entity_id: int
    note_text: str
    note_type: Optional[str] = None
    note_date: Optional[date] = None


class CaseNoteOut(CaseNoteCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------
# AUTH
# ---------------------------------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginTwoFactorOut(BaseModel):
    two_factor_required: bool = True
    temp_token: str


class VerifyOtpIn(BaseModel):
    temp_token: str
    otp_code: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
