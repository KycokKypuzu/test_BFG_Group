
"""create stock tables

Revision ID: 85b8597639e9
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "85b8597639e9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stock_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("sku", sa.String(50), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("warehouse", sa.String(50), nullable=False),
        sa.Column("operation_type", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "stock_agg",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("sku", sa.String(50), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("warehouse", sa.String(50), nullable=False),
        sa.UniqueConstraint(
            "sku",
            "warehouse",
            name="uq_products_sku_warehouse",
        ),
    )


def downgrade() -> None:
    op.drop_table("stock_agg")
    op.drop_table("stock_events")
