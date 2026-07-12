"""Product model."""

import uuid
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class StockStatus(str, PyEnum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PREORDER = "preorder"


class ProductStatus(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Product(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A sellable catalog item belonging to a single category."""

    __tablename__ = "products"

    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True, nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(150), index=True, nullable=True)

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bestseller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    new_arrival: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status = Column(
        Enum(
            ProductStatus,
            name="product_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=ProductStatus.DRAFT,
        nullable=False,
    )

    stock_status = Column(
        Enum(
            StockStatus,
            name="stock_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=StockStatus.IN_STOCK,
        nullable=False,
)

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    schema_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    og_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    creator: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.display_order"
    )
    marketplace_links: Mapped[list["ProductMarketplaceLink"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductMarketplaceLink.display_order"
    )
    videos: Mapped[list["ProductVideo"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductVideo.display_order"
    )

    @property
    def category_name(self) -> str:
        return self.category.name

    @property
    def category_slug(self) -> str:
        return self.category.slug

    @property
    def creator_name(self) -> str | None:
        return self.creator.full_name if self.creator else None
