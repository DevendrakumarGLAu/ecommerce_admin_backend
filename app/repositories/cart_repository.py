"""Data access for `Cart` and `CartItem` — a user's cart is a single aggregate."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    model = Cart

    def _cart_query(self):
        return select(Cart).options(selectinload(Cart.items).selectinload(CartItem.product))

    async def get_by_user_id(self, user_id: uuid.UUID) -> Cart | None:
        stmt = self._cart_query().where(Cart.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id_: uuid.UUID) -> Cart | None:
        stmt = self._cart_query().where(Cart.id == id_)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class CartItemRepository(BaseRepository[CartItem]):
    model = CartItem

    async def get_by_cart_and_product(self, cart_id: uuid.UUID, product_id: uuid.UUID) -> CartItem | None:
        stmt = select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_cart(self, item_id: uuid.UUID, cart_id: uuid.UUID) -> CartItem | None:
        stmt = select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_cart(self, cart_id: uuid.UUID) -> list[CartItem]:
        stmt = select(CartItem).where(CartItem.cart_id == cart_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_all_for_cart(self, cart_id: uuid.UUID) -> None:
        for item in await self.list_by_cart(cart_id):
            await self.db.delete(item)
        await self.db.flush()
