"""add resend_email_id to delivery_log

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "delivery_log",
        sa.Column("resend_email_id", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("delivery_log", "resend_email_id")
