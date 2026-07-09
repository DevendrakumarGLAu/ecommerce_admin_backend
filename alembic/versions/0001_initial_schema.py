"""Initial schema: users, categories, products, product_images, carts, cart_items, wishlist_items, settings.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="customer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'customer')", name="ck_users_role"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("image", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.String(255), nullable=True),
        sa.Column("meta_description", sa.String(500), nullable=True),
        sa.Column("meta_keywords", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_categories_id", "categories", ["id"])
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(280), nullable=False),
        sa.Column("short_description", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sku", sa.String(100), nullable=True),
        sa.Column("brand", sa.String(150), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("sale_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("buy_url", sa.String(1000), nullable=True),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("bestseller", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("new_arrival", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stock_status", sa.String(20), nullable=False, server_default="in_stock"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("seo_title", sa.String(255), nullable=True),
        sa.Column("meta_title", sa.String(255), nullable=True),
        sa.Column("meta_description", sa.String(500), nullable=True),
        sa.Column("meta_keywords", sa.String(500), nullable=True),
        sa.Column("canonical_url", sa.String(1000), nullable=True),
        sa.Column("schema_json", postgresql.JSONB(), nullable=True),
        sa.Column("og_image", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("stock_status IN ('in_stock', 'out_of_stock', 'preorder')", name="ck_products_stock_status"),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_products_status"),
    )
    op.create_index("ix_products_id", "products", ["id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_title", "products", ["title"])
    op.create_index("ix_products_slug", "products", ["slug"], unique=True)
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_brand", "products", ["brand"])

    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("image_url", sa.String(1000), nullable=False),
        sa.Column("alt_text", sa.String(255), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_product_images_id", "product_images", ["id"])
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])

    op.create_table(
        "carts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_carts_id", "carts", ["id"])
    op.create_index("ix_carts_user_id", "carts", ["user_id"], unique=True)

    op.create_table(
        "cart_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("cart_id", "product_id", name="uq_cart_item_product"),
    )
    op.create_index("ix_cart_items_id", "cart_items", ["id"])
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"])
    op.create_index("ix_cart_items_product_id", "cart_items", ["product_id"])

    op.create_table(
        "wishlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )
    op.create_index("ix_wishlist_items_id", "wishlist_items", ["id"])
    op.create_index("ix_wishlist_items_user_id", "wishlist_items", ["user_id"])
    op.create_index("ix_wishlist_items_product_id", "wishlist_items", ["product_id"])

    op.create_table(
        "settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("site_name", sa.String(150), nullable=True),
        sa.Column("logo", sa.String(500), nullable=True),
        sa.Column("favicon", sa.String(500), nullable=True),
        sa.Column("support_email", sa.String(255), nullable=True),
        sa.Column("support_phone", sa.String(20), nullable=True),
        sa.Column("facebook", sa.String(500), nullable=True),
        sa.Column("instagram", sa.String(500), nullable=True),
        sa.Column("youtube", sa.String(500), nullable=True),
        sa.Column("twitter", sa.String(500), nullable=True),
        sa.Column("google_analytics", sa.String(100), nullable=True),
        sa.Column("facebook_pixel", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_settings_id", "settings", ["id"])


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("wishlist_items")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("product_images")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("users")
