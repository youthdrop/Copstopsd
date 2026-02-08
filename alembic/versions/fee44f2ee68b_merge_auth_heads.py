"""merge auth heads

Revision ID: fee44f2ee68b
Revises: 54373626066e, c07b368db0b0
Create Date: 2026-02-07 23:17:27.123567

"""

from alembic import op
import sqlalchemy as sa

revision = 'fee44f2ee68b'
down_revision = ('54373626066e', 'c07b368db0b0')
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
