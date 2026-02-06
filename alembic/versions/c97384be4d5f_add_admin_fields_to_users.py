"""add admin fields to users

Revision ID: c97384be4d5f
Revises: e0ad03a89373
Create Date: 2026-02-05 17:31:07.691701
"""

from alembic import op
import sqlalchemy as sa

revision = "c97384be4d5f"
down_revision = "e0ad03a89373"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns if they don't exist (Postgres-safe)
    op.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);')
    op.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;')
    op.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;')

    # If you *previously* stored passwords in a different column name, you can migrate it here.
    # Example (only if needed — uncomment if your old column exists and has data):
    # op.execute('UPDATE users SET password_hash = hashed_password WHERE password_hash IS NULL;')


def downgrade() -> None:
    # Reverse (drops)
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_admin;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_active;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS password_hash;")
