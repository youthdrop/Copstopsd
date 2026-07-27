"""add password reset fields to users

Revision ID: 8f31c2d4e5a6
Revises: 7d9b4f2a1c30
"""

from alembic import op
import sqlalchemy as sa


revision = "8f31c2d4e5a6"
down_revision = "7d9b4f2a1c30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("reset_otp_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("reset_otp_expires_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "reset_otp_expires_at")
    op.drop_column("users", "reset_otp_hash")
