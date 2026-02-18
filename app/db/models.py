from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    Time,
    Text,
    ForeignKey,
    Boolean,
    func,
    UniqueConstraint,
    Table,
    Column,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# -----------------------------
# Many-to-many join table
# -----------------------------
complaint_officers = Table(
    "complaint_officers",
    Base.metadata,
    Column("complaint_id", ForeignKey("complaints.id"), primary_key=True),
    Column("officer_id", ForeignKey("officers.id"), primary_key=True),
    UniqueConstraint("complaint_id", "officer_id", name="uq_complaint_officer"),
)


# -----------------------------
# CaseNote (for complaint/officer notes)
# -----------------------------
class CaseNote(Base):
    __tablename__ = "case_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)  # "complaint" | "officer"
    entity_id: Mapped[int] = mapped_column(Integer, index=True)

    note_text: Mapped[str] = mapped_column(Text)
    note_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    note_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# -----------------------------
# Complaint
# -----------------------------
class Complaint(Base):
    """
    Complaint record stored in the database.

    Canonical "harms done" storage:
      - harm_types: TEXT[]  (Postgres array)
    Legacy:
      - harm_done: TEXT (comma-separated string, kept for backward compatibility)
    """
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # where it came from (web/mobile)
    source: Mapped[str] = mapped_column(String(32), default="web")

    complainant_first_name: Mapped[str] = mapped_column(String(128))
    complainant_last_name: Mapped[str] = mapped_column(String(128))

    complainant_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ✅ canonical phone field
    complainant_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    stop_date: Mapped[date] = mapped_column(Date)

    # ✅ time of stop (optional)
    stop_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    department: Mapped[str] = mapped_column(String(128))
    unit: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    stop_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ✅ canonical harms (array)
    harm_types: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
    )

    # legacy harms string
    harm_done: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))

    badge_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

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
