"""add otp_hash and is_verified to users

Revision ID: c07b368db0b0
Revises: eec40c84ccf5
Create Date: 2026-02-07 23:02:15.805999
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c07b368db0b0"
down_revision = "eec40c84ccf5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename tp_hash -> otp_hash if tp_hash exists
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='tp_hash'
            ) THEN
                ALTER TABLE users RENAME COLUMN tp_hash TO otp_hash;
            END IF;
        END$$;
        """
    )

    # Add otp_hash if it doesn't exist (covers envs where tp_hash never existed)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='otp_hash'
            ) THEN
                ALTER TABLE users ADD COLUMN otp_hash VARCHAR(255);
            END IF;
        END$$;
        """
    )

    # Add otp_expires_at if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='otp_expires_at'
            ) THEN
                ALTER TABLE users ADD COLUMN otp_expires_at TIMESTAMPTZ;
            END IF;
        END$$;
        """
    )

    # Add otp_requested_at if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='otp_requested_at'
            ) THEN
                ALTER TABLE users ADD COLUMN otp_requested_at TIMESTAMPTZ;
            END IF;
        END$$;
        """
    )

    # Add is_verified if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='is_verified'
            ) THEN
                ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Dev-friendly downgrade
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_verified;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS otp_requested_at;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS otp_expires_at;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS otp_hash;")
