"""add complaint assignment fields

Revision ID: 7d9b4f2a1c30
Revises: 082da1d83a8d
Create Date: 2026-07-26
"""
from alembic import op
import sqlalchemy as sa

revision = "7d9b4f2a1c30"
down_revision = "082da1d83a8d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("complaints", sa.Column("assigned_to_id", sa.Integer(), nullable=True))
    op.add_column("complaints", sa.Column("assigned_by_id", sa.Integer(), nullable=True))
    op.add_column("complaints", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("complaints", sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False))
    op.add_column("complaints", sa.Column("due_date", sa.Date(), nullable=True))
    op.create_index("ix_complaints_assigned_to_id", "complaints", ["assigned_to_id"], unique=False)
    op.create_index("ix_complaints_due_date", "complaints", ["due_date"], unique=False)
    op.create_foreign_key("fk_complaints_assigned_to_users", "complaints", "users", ["assigned_to_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_complaints_assigned_by_users", "complaints", "users", ["assigned_by_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_complaints_assigned_by_users", "complaints", type_="foreignkey")
    op.drop_constraint("fk_complaints_assigned_to_users", "complaints", type_="foreignkey")
    op.drop_index("ix_complaints_due_date", table_name="complaints")
    op.drop_index("ix_complaints_assigned_to_id", table_name="complaints")
    op.drop_column("complaints", "due_date")
    op.drop_column("complaints", "priority")
    op.drop_column("complaints", "assigned_at")
    op.drop_column("complaints", "assigned_by_id")
    op.drop_column("complaints", "assigned_to_id")
