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
    Table,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# -----------------------------
# User (for auth)
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ✅ account flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # ✅ needed by auth.py

    # ✅ OTP fields (fix: otp_hash name must match auth.py)
    otp_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    otp_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# -----------------------------
# Association table (many-to-many)
#
# IMPORTANT:
# The database table `complaint_officers` does NOT have an `id` column.
# It uses a composite primary key (complaint_id, officer_id).
# -----------------------------
complaint_officers = Table(
    "complaint_officers",
    Base.metadata,
    Column("complaint_id", ForeignKey("complaints.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("officer_id", ForeignKey("officers.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
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

    complainant_first_name: Mapped[str] = mapped_column(String(128))
    complainant_last_name: Mapped[str] = mapped_column(String(128))
    complainant_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    complainant_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    stop_date: Mapped[date] = mapped_column(Date)
    department: Mapped[str] = mapped_column(String(128))
    unit: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    stop_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    narrative: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="open")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    officers: Mapped[list["Officer"]] = relationship(
        "Officer",
        secondary=complaint_officers,
        back_populates="complaints",
        lazy="selectin",
    )

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
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[str] = mapped_column(String(128))
    badge_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    complaints: Mapped[list["Complaint"]] = relationship(
        "Complaint",
        secondary=complaint_officers,
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

    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)

    note_text: Mapped[str] = mapped_column(Text)
    note_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    note_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # ✅ DO NOT define updated_at because the DB table does not have it
