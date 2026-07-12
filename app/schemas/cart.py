"""Cart and cart-item request/response schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=999)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=999)


class CartItemProduct(BaseModel):
    """Minimal product snapshot embedded in a cart item response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    price: Decimal
    sale_price: Decimal | None
    og_image: str | None
    stock_status: str


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product: CartItemProduct
    quantity: int
    line_total: Decimal


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    items: list[CartItemResponse]
    total_items: int
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
