"""Product marketplace link model — where a product can be bought (Amazon, Flipkart, Meesho, etc.)."""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class MarketplacePlatform(str, PyEnum):
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    MEESHO = "meesho"
    MYNTRA = "myntra"
    SNAPDEAL = "snapdeal"
    OTHER = "other"


class ProductMarketplaceLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single "buy it here" link for a product on a given marketplace."""

    __tablename__ = "product_marketplace_links"

    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    platform: Mapped[MarketplacePlatform] = mapped_column(
    Enum(
        MarketplacePlatform,
        name="marketplace_platform",
        native_enum=False,
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
    ),
    nullable=False,
)
    # Required when platform == OTHER (e.g. "Official Website"); ignored/blank otherwise.
    custom_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="marketplace_links")
