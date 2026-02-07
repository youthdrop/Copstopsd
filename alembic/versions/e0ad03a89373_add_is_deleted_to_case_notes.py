"""add is_deleted to case_notes

Revision ID: e0ad03a89373
Revises: 8ca14584723f
Create Date: 2026-02-05 14:31:00.211205
"""

from alembic import op
import sqlalchemy as sa


revision = "e0ad03a89373"
down_revision = "8ca14584723f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "case_notes",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("case_notes", "is_deleted")
