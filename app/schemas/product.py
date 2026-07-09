"""Product, product-image, and marketplace-link request/response schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer, model_validator

from app.models.product import ProductStatus, StockStatus
from app.models.product_marketplace_link import MarketplacePlatform
from app.schemas.category import CategoryResponse


class ProductImageCreate(BaseModel):
    """Attach an already-uploaded image (via /uploads/image) to a product."""

    image_url: HttpUrl
    alt_text: str | None = Field(default=None, max_length=255)
    display_order: int = Field(default=0, ge=0)

    @field_serializer("image_url")
    def serialize_url(self, value: HttpUrl) -> str:
        return str(value)


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    alt_text: str | None
    display_order: int


class ProductVideoCreate(BaseModel):
    """Attach an already-uploaded video (via /uploads/video) to a product."""

    video_url: HttpUrl
    thumbnail_url: HttpUrl | None = None
    caption: str | None = Field(default=None, max_length=255)
    display_order: int = Field(default=0, ge=0)

    @field_serializer("video_url", "thumbnail_url")
    def serialize_urls(self, value: HttpUrl | None) -> str | None:
        return str(value) if value is not None else None


class ProductVideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_url: str
    thumbnail_url: str | None
    caption: str | None
    display_order: int


class MarketplaceLinkCreate(BaseModel):
    """A "buy it here" link to attach to a product (e.g. Amazon, Flipkart, Meesho)."""

    platform: MarketplacePlatform
    custom_label: str | None = Field(default=None, max_length=100)
    url: HttpUrl
    display_order: int = Field(default=0, ge=0)

    @field_serializer("url")
    def serialize_url(self, value: HttpUrl) -> str:
        return str(value)

    @model_validator(mode="after")
    def validate_custom_label(self) -> "MarketplaceLinkCreate":
        if self.platform == MarketplacePlatform.OTHER and not self.custom_label:
            raise ValueError("custom_label is required when platform is 'other'")
        return self


class MarketplaceLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    platform: MarketplacePlatform
    custom_label: str | None
    url: str
    display_order: int


class ProductBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    sku: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=150)
    price: Decimal = Field(..., gt=0, description="Regular price, must be greater than 0")
    sale_price: Decimal | None = Field(default=None, gt=0)
    featured: bool = False
    bestseller: bool = False
    new_arrival: bool = False
    stock_status: StockStatus = StockStatus.IN_STOCK
    status: ProductStatus = ProductStatus.DRAFT

    seo_title: str | None = Field(default=None, max_length=255)
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)
    meta_keywords: str | None = Field(default=None, max_length=500)
    canonical_url: HttpUrl | None = None
    schema_json: dict[str, Any] | None = None
    og_image: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_sale_price(self) -> "ProductBase":
        if self.sale_price is not None and self.sale_price >= self.price:
            raise ValueError("sale_price must be lower than price")
        return self


class ProductCreate(ProductBase):
    category_id: uuid.UUID


class ProductUpdate(BaseModel):
    """Admin payload to update a product. All fields optional (PATCH semantics)."""

    category_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    sku: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=150)
    price: Decimal | None = Field(default=None, gt=0)
    sale_price: Decimal | None = Field(default=None, gt=0)
    featured: bool | None = None
    bestseller: bool | None = None
    new_arrival: bool | None = None
    stock_status: StockStatus | None = None
    status: ProductStatus | None = None

    seo_title: str | None = Field(default=None, max_length=255)
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)
    meta_keywords: str | None = Field(default=None, max_length=500)
    canonical_url: HttpUrl | None = None
    schema_json: dict[str, Any] | None = None
    og_image: HttpUrl | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: CategoryResponse
    title: str
    slug: str
    short_description: str | None
    description: str | None
    sku: str | None
    brand: str | None
    price: Decimal
    sale_price: Decimal | None
    featured: bool
    bestseller: bool
    new_arrival: bool
    stock_status: StockStatus
    status: ProductStatus

    seo_title: str | None
    meta_title: str | None
    meta_description: str | None
    meta_keywords: str | None
    canonical_url: str | None
    schema_json: dict[str, Any] | None
    image: str | None = None

    images: list[ProductImageResponse] = []
    videos: list[ProductVideoResponse] = []
    marketplace_links: list[MarketplaceLinkResponse] = []
    created_at: datetime
    updated_at: datetime


class ProductSummaryResponse(BaseModel):
    """Lightweight representation used in listing endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    brand: str | None
    category_name: str
    category_slug: str
    price: Decimal
    sale_price: Decimal | None
    featured: bool
    bestseller: bool
    new_arrival: bool
    stock_status: StockStatus
    status: ProductStatus
    images: list[ProductImageResponse] = []
    created_at: datetime
