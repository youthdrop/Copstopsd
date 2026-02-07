"""add full_name to users

Revision ID: 1fe376ef9bb4
Revises: c97384be4d5f
Create Date: 2026-02-06 22:49:20.321691
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1fe376ef9bb4"
down_revision = "c97384be4d5f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("users", "full_name")
