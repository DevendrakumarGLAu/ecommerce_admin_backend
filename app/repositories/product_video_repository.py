"""Data access for `ProductVideo` records."""

import uuid

from sqlalchemy import select

from app.models.product_video import ProductVideo
from app.repositories.base import BaseRepository


class ProductVideoRepository(BaseRepository[ProductVideo]):
    model = ProductVideo

    async def list_by_product(self, product_id: uuid.UUID) -> list[ProductVideo]:
        stmt = (
            select(ProductVideo)
            .where(ProductVideo.product_id == product_id)
            .order_by(ProductVideo.display_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
