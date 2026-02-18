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
    complainant_phone: Optional[str] = None  # ✅ phone

    stop_date: date
    stop_time: Optional[str] = None  # ✅ NEW: accepts "HH:MM"

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    narrative: str
    officer_ids: Optional[List[int]] = None


class ComplaintOut(BaseModel):
    id: int
    case_number: str
    source: Optional[str] = None

    complainant_first_name: str
    complainant_last_name: str
    complainant_email: Optional[EmailStr] = None
    complainant_phone: Optional[str] = None  # ✅ phone returned

    stop_date: date

    # ✅ store as time in DB, but serialize cleanly for JS
    stop_time: Optional[time] = None

    @field_serializer("stop_time")
    def _serialize_stop_time(self, v: Optional[time], _info: Any) -> Optional[str]:
        # Frontend-friendly "HH:MM"
        return v.strftime("%H:%M") if v else None

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    # ✅ NEW
    harm_done: Optional[str] = None

    # ✅ allow null because mobile intake removed narrative
    narrative: Optional[str] = None

    status: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # ✅ officers involved
    officers: List[OfficerOut] = []

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
    stop_time: Optional[str] = None  # ✅ allow time on public intake too

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    narrative: str
    officer_ids: Optional[List[int]] = None


# ---------------------------------
# Case Notes
# ---------------------------------
class CaseNoteCreate(BaseModel):
    entity_type: str  # "complaint" or "officer"
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
