"""no-op: users table already exists (legacy migration)

Revision ID: 1b05d0735127
Revises: 0001_init
Create Date: 2026-01-??  (kept for history)

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1b05d0735127"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    This migration was created later but duplicates the `users` table that already
    exists from the baseline schema. Keeping as a no-op so Alembic doesn't try
    to re-create tables in existing databases.
    """
    pass


def downgrade() -> None:
    pass
