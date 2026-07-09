"""Data access for `ProductMarketplaceLink` records."""

import uuid

from sqlalchemy import select

from app.models.product_marketplace_link import ProductMarketplaceLink
from app.repositories.base import BaseRepository


class ProductMarketplaceLinkRepository(BaseRepository[ProductMarketplaceLink]):
    model = ProductMarketplaceLink

    async def list_by_product(self, product_id: uuid.UUID) -> list[ProductMarketplaceLink]:
        stmt = (
            select(ProductMarketplaceLink)
            .where(ProductMarketplaceLink.product_id == product_id)
            .order_by(ProductMarketplaceLink.display_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
