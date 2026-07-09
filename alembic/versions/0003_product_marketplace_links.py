"""Replace products.buy_url with a product_marketplace_links table.

Revision ID: 0003_product_marketplace_links
Revises: 0002_add_user_avatar
Create Date: 2026-07-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_product_marketplace_links"
down_revision: Union[str, None] = "0002_add_user_avatar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_marketplace_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("custom_label", sa.String(100), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "platform IN ('amazon', 'flipkart', 'meesho', 'myntra', 'snapdeal', 'other')",
            name="ck_product_marketplace_links_platform",
        ),
    )
    op.create_index("ix_product_marketplace_links_id", "product_marketplace_links", ["id"])
    op.create_index("ix_product_marketplace_links_product_id", "product_marketplace_links", ["product_id"])

    op.drop_column("products", "buy_url")


def downgrade() -> None:
    op.add_column("products", sa.Column("buy_url", sa.String(1000), nullable=True))
    op.drop_table("product_marketplace_links")
