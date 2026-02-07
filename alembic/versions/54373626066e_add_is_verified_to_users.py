"""add is_verified to users

Revision ID: 54373626066e
Revises: 1fe376ef9bb4
Create Date: 2026-02-07 10:00:24.191118

"""

from alembic import op
import sqlalchemy as sa

revision = '54373626066e'
down_revision = '1fe376ef9bb4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "NEW_ID"
down_revision = "1fe376ef9bb4"  # <-- your current latest revision
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("users", "is_verified")
