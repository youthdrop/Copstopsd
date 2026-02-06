from __future__ import annotations

from datetime import date, datetime
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
# Complaints
# ---------------------------------
class ComplaintCreate(BaseModel):
    complainant_first_name: str
    complainant_last_name: str
    complainant_email: Optional[EmailStr] = None

    # ✅ ADD THIS (matches DB column complainant_phone)
    complainant_phone: Optional[str] = None

    stop_date: date
    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None
    narrative: str

    # optional linking to officers (your frontend supports this)
    officer_ids: Optional[List[int]] = None


class ComplaintOut(BaseModel):
    id: int
    case_number: str
    source: Optional[str] = None

    complainant_first_name: str
    complainant_last_name: str
    complainant_email: Optional[EmailStr] = None

    # ✅ ADD THIS (so API returns it too)
    complainant_phone: Optional[str] = None

    stop_date: date
    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    narrative: str
    status: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # nested relationships
    officers: List[OfficerOut] = []

    class Config:
        from_attributes = True


# ---------------------------------
# Public intake (mobile/web public form)
# ---------------------------------
class ComplaintPublicCreate(BaseModel):
    name: str = Field(..., description="Complainant name (best-effort parsed into first/last)")
    email: Optional[EmailStr] = None

    # ✅ ADD THIS for public intake too (optional)
    complainant_phone: Optional[str] = None

    stop_date: date
    department: str
    unit: Optional[str] = None
    stop_location: Optional[str] = None

    narrative: str

    # Optional officer linking if your public form supports it
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
# AUTH (for your /auth routes)
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
    otp_code: str  # "123456"


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
