"""add delivery_log table

Revision ID: b1c2d3e4f5a6
Revises: 497b4b85e0d7
Create Date: 2026-04-09 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "497b4b85e0d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_log",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sent_date", sa.Date(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sent_date", "channel", name="uq_delivery_log_date_channel"),
    )
    op.create_index(
        op.f("ix_delivery_log_sent_date"), "delivery_log", ["sent_date"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_delivery_log_sent_date"), table_name="delivery_log")
    op.drop_table("delivery_log")
