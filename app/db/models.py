from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


# -----------------------------
# User (for auth)
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # IMPORTANT:
    # Your DB does NOT have users.hashed_password (error proves it).
    # Most likely it has users.password_hash, so we map to that.
    password_hash: Mapped[str] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Backwards-compatible alias so any existing code that uses
    # user.hashed_password keeps working.
    @property
    def hashed_password(self) -> str:
        return self.password_hash

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        self.password_hash = value

    otp_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    otp_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# -----------------------------
# Association table
# -----------------------------
class ComplaintOfficer(Base):
    __tablename__ = "complaint_officers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    officer_id: Mapped[int] = mapped_column(ForeignKey("officers.id"), index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("complaint_id", "officer_id", name="uq_complaint_officer"),
    )


# -----------------------------
# Complaint
# -----------------------------
class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(32), default="web")

    complainant_first_name: Mapped[str] = mapped_column(String(120))
    complainant_last_name: Mapped[str] = mapped_column(String(120))
    complainant_email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    complainant_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    stop_date: Mapped[date] = mapped_column(Date)
    department: Mapped[str] = mapped_column(String(120))
    unit: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    stop_location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    narrative: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="open")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    officers: Mapped[list["Officer"]] = relationship(
        "Officer",
        secondary="complaint_officers",
        back_populates="complaints",
        lazy="selectin",
    )

    # NOTE:
    # This relationship is viewonly and keyed on entity_type/entity_id.
    # We removed CaseNote.is_deleted from the model because your DB doesn't have it.
    case_notes: Mapped[list["CaseNote"]] = relationship(
        "CaseNote",
        primaryjoin="and_(CaseNote.entity_type=='complaint', foreign(CaseNote.entity_id)==Complaint.id)",
        viewonly=True,
        lazy="selectin",
    )


# -----------------------------
# Officer
# -----------------------------
class Officer(Base):
    __tablename__ = "officers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    badge_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    department: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    complaints: Mapped[list["Complaint"]] = relationship(
        "Complaint",
        secondary="complaint_officers",
        back_populates="officers",
        lazy="selectin",
    )

    case_notes: Mapped[list["CaseNote"]] = relationship(
        "CaseNote",
        primaryjoin="and_(CaseNote.entity_type=='officer', foreign(CaseNote.entity_id)==Officer.id)",
        viewonly=True,
        lazy="selectin",
    )


# -----------------------------
# Case Notes (polymorphic by entity_type + entity_id)
# -----------------------------
class CaseNote(Base):
    __tablename__ = "case_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    entity_type: Mapped[str] = mapped_column(String(32))  # "complaint" or "officer"
    entity_id: Mapped[int] = mapped_column(Integer, index=True)

    note_text: Mapped[str] = mapped_column(Text)
    note_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    note_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("id", name="uq_case_notes_id"),
    )
