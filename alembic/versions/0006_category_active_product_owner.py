"""Add is_active to categories, created_by to products.

Revision ID: 0006_category_active_product_owner
Revises: 0005_settings_hero_banner
Create Date: 2026-07-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_category_active_owner"
down_revision: Union[str, None] = "0005_settings_hero_banner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("categories", "is_active", server_default=None)

    op.add_column(
        "products",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(op.f("ix_products_created_by"), "products", ["created_by"])
    op.create_foreign_key(
        "fk_products_created_by_users",
        "products",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_products_created_by_users", "products", type_="foreignkey")
    op.drop_index(op.f("ix_products_created_by"), table_name="products")
    op.drop_column("products", "created_by")
    op.drop_column("categories", "is_active")
