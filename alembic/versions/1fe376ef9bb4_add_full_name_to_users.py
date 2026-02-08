"""add full_name to users (idempotent)

Revision ID: 1fe376ef9bb4
Revises: <KEEP_YOUR_CURRENT_DOWN_REVISION>
Create Date: <KEEP_EXISTING_DATE>
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1fe376ef9bb4"
down_revision = "1b05d0735127"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Postgres-safe: add column only if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='full_name'
            ) THEN
                ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Dev-friendly downgrade
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS full_name;")
