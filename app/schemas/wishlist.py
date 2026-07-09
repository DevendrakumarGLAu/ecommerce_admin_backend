"""Wishlist request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.product import ProductSummaryResponse


class WishlistCreate(BaseModel):
    product_id: uuid.UUID


class WishlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product: ProductSummaryResponse
    created_at: datetime
