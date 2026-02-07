"""add is_verified to users"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "54373626066e"
down_revision = "1fe376ef9bb4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column("users", "is_verified")
