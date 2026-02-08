"""merge final heads

Revision ID: 082da1d83a8d
Revises: c97384be4d5f, fee44f2ee68b
Create Date: 2026-02-07 23:24:25.007539

"""

from alembic import op
import sqlalchemy as sa

revision = '082da1d83a8d'
down_revision = ('c97384be4d5f', 'fee44f2ee68b')
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
