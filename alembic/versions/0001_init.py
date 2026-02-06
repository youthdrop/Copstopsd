"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-06

"""

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "officers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("badge_number", sa.String(length=64), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("unit", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_officers_name", "officers", ["last_name", "first_name"])
    op.create_index("ix_officers_dept_badge", "officers", ["department", "badge_number"])

    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_number", sa.String(length=32), nullable=False, unique=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="web"),
        sa.Column("complainant_first_name", sa.String(length=120), nullable=False),
        sa.Column("complainant_last_name", sa.String(length=120), nullable=False),
        sa.Column("complainant_email", sa.String(length=256), nullable=True),
        sa.Column("complainant_phone", sa.String(length=64), nullable=True),
        sa.Column("stop_date", sa.Date(), nullable=False),
        sa.Column("stop_location", sa.String(length=512), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("unit", sa.String(length=120), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="New"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_complaints_case_number", "complaints", ["case_number"])
    op.create_index("ix_complaints_complainant", "complaints", ["complainant_last_name", "complainant_first_name"])
    op.create_index("ix_complaints_stop_date", "complaints", ["stop_date"])

    op.create_table(
        "complaint_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("label", sa.String(length=120), nullable=False),
    )

    op.create_table(
        "complaint_type_links",
        sa.Column("complaint_id", sa.Integer(), sa.ForeignKey("complaints.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("complaint_type_id", sa.Integer(), sa.ForeignKey("complaint_types.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "complaint_officers",
        sa.Column("complaint_id", sa.Integer(), sa.ForeignKey("complaints.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("officer_id", sa.Integer(), sa.ForeignKey("officers.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "case_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("note_type", sa.String(length=64), nullable=True),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("note_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_case_notes_entity", "case_notes", ["entity_type", "entity_id"])

    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("complaint_id", sa.Integer(), sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=256), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("uploaded_by", sa.String(length=256), nullable=True),
    )
    op.create_index("ix_attachments_complaint", "attachments", ["complaint_id"])

    # seed complaint types
    op.execute("INSERT INTO complaint_types (code, label) VALUES "
               "('TICKET','Ticket'),"
               "('SEARCH','Search'),"
               "('DETAINMENT','Detainment'),"
               "('ARREST','Arrest'),"
               "('USE_OF_FORCE','Use of force');")


def downgrade() -> None:
    op.drop_index("ix_attachments_complaint", table_name="attachments")
    op.drop_table("attachments")

    op.drop_index("ix_case_notes_entity", table_name="case_notes")
    op.drop_table("case_notes")

    op.drop_table("complaint_officers")
    op.drop_table("complaint_type_links")
    op.drop_table("complaint_types")

    op.drop_index("ix_complaints_stop_date", table_name="complaints")
    op.drop_index("ix_complaints_complainant", table_name="complaints")
    op.drop_index("ix_complaints_case_number", table_name="complaints")
    op.drop_table("complaints")

    op.drop_index("ix_officers_dept_badge", table_name="officers")
    op.drop_index("ix_officers_name", table_name="officers")
    op.drop_table("officers")
