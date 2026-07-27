"""add complaint pipeline stage and next action

Revision ID: a4c92f7d1e61
Revises: 8f31c2d4e5a6
"""

from alembic import op
import sqlalchemy as sa

revision = "a4c92f7d1e61"
down_revision = "8f31c2d4e5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "complaints",
        sa.Column("pipeline_stage", sa.String(length=64), server_default="new", nullable=False),
    )
    op.add_column("complaints", sa.Column("next_action", sa.Text(), nullable=True))
    op.create_index("ix_complaints_pipeline_stage", "complaints", ["pipeline_stage"], unique=False)
    op.execute("UPDATE complaints SET pipeline_stage = 'assigned' WHERE assigned_to_id IS NOT NULL")
    op.execute("UPDATE complaints SET pipeline_stage = 'closed' WHERE lower(status) = 'closed'")


def downgrade() -> None:
    op.drop_index("ix_complaints_pipeline_stage", table_name="complaints")
    op.drop_column("complaints", "next_action")
    op.drop_column("complaints", "pipeline_stage")
