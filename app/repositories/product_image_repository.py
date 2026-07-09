"""Data access for `ProductImage` records."""

import uuid

from sqlalchemy import select

from app.models.product_image import ProductImage
from app.repositories.base import BaseRepository


class ProductImageRepository(BaseRepository[ProductImage]):
    model = ProductImage

    async def list_by_product(self, product_id: uuid.UUID) -> list[ProductImage]:
        stmt = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.display_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
