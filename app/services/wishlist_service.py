"""Business logic for the wishlist (a user-to-product many-to-many join)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.product_repository import ProductRepository
from app.repositories.wishlist_repository import WishlistRepository
from app.schemas.wishlist import WishlistResponse
from app.utils.exceptions import ConflictException, NotFoundException


class WishlistService:
    """Orchestrates adding, removing, and listing a user's wishlist entries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.wishlist = WishlistRepository(db)
        self.products = ProductRepository(db)

    async def add(self, user_id: uuid.UUID, product_id: uuid.UUID) -> WishlistResponse:
        product = await self.products.get_by_id_active(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        if await self.wishlist.get_by_user_and_product(user_id, product_id):
            raise ConflictException("Product is already in your wishlist")

        entry = await self.wishlist.create(user_id=user_id, product_id=product_id)
        await self.wishlist.commit()
        entry.product = product
        return WishlistResponse.model_validate(entry)

    async def remove(self, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
        entry = await self.wishlist.get_by_user_and_product(user_id, product_id)
        if entry is None:
            raise NotFoundException("Wishlist entry not found")

        await self.wishlist.delete(entry)
        await self.wishlist.commit()

    async def list_for_user(self, user_id: uuid.UUID) -> list[WishlistResponse]:
        entries = await self.wishlist.list_by_user(user_id)
        return [WishlistResponse.model_validate(entry) for entry in entries]
