"""Business logic for the shopping cart. Each user owns exactly one cart."""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart
from app.models.product import ProductStatus, StockStatus
from app.repositories.cart_repository import CartItemRepository, CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemCreate, CartItemProduct, CartItemResponse, CartItemUpdate, CartResponse
from app.utils.exceptions import BadRequestException, NotFoundException


class CartService:
    """Orchestrates cart retrieval and item add/update/remove/clear operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.carts = CartRepository(db)
        self.items = CartItemRepository(db)
        self.products = ProductRepository(db)

    async def _get_or_create_cart(self, user_id: uuid.UUID) -> Cart:
        cart = await self.carts.get_by_user_id(user_id)
        if cart is not None:
            return cart

        await self.carts.create(user_id=user_id)
        await self.carts.commit()
        return await self.carts.get_by_user_id(user_id)

    @staticmethod
    def _to_response(cart: Cart) -> CartResponse:
        item_responses = [
            CartItemResponse(
                id=item.id,
                product=CartItemProduct.model_validate(item.product),
                quantity=item.quantity,
                line_total=(item.product.sale_price or item.product.price) * item.quantity,
            )
            for item in cart.items
        ]
        subtotal = sum((r.line_total for r in item_responses), Decimal("0"))
        return CartResponse(
            id=cart.id,
            items=item_responses,
            total_items=sum(i.quantity for i in cart.items),
            subtotal=subtotal,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    async def get_cart(self, user_id: uuid.UUID) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)
        return self._to_response(cart)

    async def add_item(self, user_id: uuid.UUID, payload: CartItemCreate) -> CartResponse:
        """Add a product to the cart, or increment its quantity if already present."""
        product = await self.products.get_by_id_active(payload.product_id)
        if product is None:
            raise NotFoundException("Product not found")
        if product.status != ProductStatus.PUBLISHED:
            raise BadRequestException("Product is not available for purchase")
        if product.stock_status == StockStatus.OUT_OF_STOCK:
            raise BadRequestException("Product is out of stock")

        cart = await self._get_or_create_cart(user_id)
        existing = await self.items.get_by_cart_and_product(cart.id, payload.product_id)
        if existing:
            await self.items.update(existing, quantity=existing.quantity + payload.quantity)
        else:
            await self.items.create(cart_id=cart.id, product_id=payload.product_id, quantity=payload.quantity)
        await self.items.commit()

        return self._to_response(await self.carts.get_by_id(cart.id))

    async def update_item(self, user_id: uuid.UUID, item_id: uuid.UUID, payload: CartItemUpdate) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)
        item = await self.items.get_by_id_and_cart(item_id, cart.id)
        if item is None:
            raise NotFoundException("Cart item not found")

        await self.items.update(item, quantity=payload.quantity)
        await self.items.commit()
        return self._to_response(await self.carts.get_by_id(cart.id))

    async def remove_item(self, user_id: uuid.UUID, item_id: uuid.UUID) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)
        item = await self.items.get_by_id_and_cart(item_id, cart.id)
        if item is None:
            raise NotFoundException("Cart item not found")

        await self.items.delete(item)
        await self.items.commit()
        return self._to_response(await self.carts.get_by_id(cart.id))

    async def clear_cart(self, user_id: uuid.UUID) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)
        await self.items.delete_all_for_cart(cart.id)
        await self.items.commit()
        return self._to_response(await self.carts.get_by_id(cart.id))
