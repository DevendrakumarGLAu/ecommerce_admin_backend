"""Data access for `Wishlist` entries."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.wishlist import Wishlist
from app.repositories.base import BaseRepository


class WishlistRepository(BaseRepository[Wishlist]):
    model = Wishlist

    async def get_by_user_and_product(self, user_id: uuid.UUID, product_id: uuid.UUID) -> Wishlist | None:
        stmt = select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(self, wishlist_id: uuid.UUID, user_id: uuid.UUID) -> Wishlist | None:
        stmt = select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Wishlist]:
        stmt = (
            select(Wishlist)
            .options(selectinload(Wishlist.product))
            .where(Wishlist.user_id == user_id)
            .order_by(Wishlist.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
