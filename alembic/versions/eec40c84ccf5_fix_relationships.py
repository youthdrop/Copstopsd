"""fix relationships

Revision ID: eec40c84ccf5
Revises: 0001_init
Create Date: 2026-01-06 21:45:39.487124

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "eec40c84ccf5"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    This migration was auto-generated incorrectly (it attempted to drop core tables on upgrade
    and also had indentation issues). For development, the schema created in 0001_init is the
    desired baseline, so this revision is intentionally a no-op.
    """
    pass


def downgrade() -> None:
    # No-op (dev)
    pass
