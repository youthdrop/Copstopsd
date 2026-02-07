"""add phone number to complaints

Revision ID: 8ca14584723f
Revises: 1b05d0735127
Create Date: 2026-02-04 20:10:00.780299
"""

from alembic import op
import sqlalchemy as sa


revision = "8ca14584723f"
down_revision = "1b05d0735127"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "complaints",
        sa.Column("phone_number", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("complaints", "phone_number")
