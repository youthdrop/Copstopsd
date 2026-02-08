"""add is_verified to users"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "54373626066e"
down_revision = "1fe376ef9bb4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # no-op: handled in later consolidated migration
    pass

def downgrade() -> None:
    pass


