from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


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
# ---------------------------------
# Complaints
# ---------------------------------
class ComplaintCreate(BaseModel):
    complainant_first_name: str
    complainant_last_name: str
    complainant_email: Optional[EmailStr] = None
    complainant_phone: Optional[str] = None

    stop_date: date
    stop_time: Optional[str] = None  # ✅ NEW: "HH:MM"

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    narrative: str
    officer_ids: Optional[List[int]] = None


class ComplaintOut(BaseModel):
    id: int
    case_number: str

    complainant_first_name: str
    complainant_last_name: str
    complainant_email: Optional[EmailStr] = None
    complainant_phone: Optional[str] = None

    stop_date: date
    stop_time: Optional[str] = None  # ✅ return as string or switch to time later

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    harm_done: Optional[str] = None
    narrative: Optional[str] = None
    status: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    stop_time: Optional[str] = None  # ✅ allow time here too

    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    narrative: str
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
