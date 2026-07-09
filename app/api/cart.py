"""Cart endpoints — authenticated users manage their own single cart."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.schemas.common import SuccessResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get(
    "",
    response_model=SuccessResponse[CartResponse],
    summary="Get the current user's cart",
    description="Returns the authenticated user's cart, creating an empty one if it doesn't exist yet.",
)
async def get_cart(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SuccessResponse[CartResponse]:
    cart = await CartService(db).get_cart(current_user.id)
    return SuccessResponse(data=cart)


@router.post(
    "/items",
    response_model=SuccessResponse[CartResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to the cart",
    description="Adds a product to the cart, or increases its quantity if already present.",
)
async def add_item(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[CartResponse]:
    cart = await CartService(db).add_item(current_user.id, payload)
    return SuccessResponse(message="Item added to cart", data=cart)


@router.put(
    "/items/{item_id}",
    response_model=SuccessResponse[CartResponse],
    summary="Update a cart item's quantity",
    description="Sets the exact quantity for a single cart item.",
)
async def update_item(
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[CartResponse]:
    cart = await CartService(db).update_item(current_user.id, item_id, payload)
    return SuccessResponse(message="Cart item updated", data=cart)


@router.delete(
    "/items/{item_id}",
    response_model=SuccessResponse[CartResponse],
    summary="Remove an item from the cart",
    description="Removes a single item from the cart.",
)
async def remove_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[CartResponse]:
    cart = await CartService(db).remove_item(current_user.id, item_id)
    return SuccessResponse(message="Item removed from cart", data=cart)


@router.delete(
    "",
    response_model=SuccessResponse[CartResponse],
    summary="Clear the cart",
    description="Removes all items from the authenticated user's cart.",
)
async def clear_cart(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SuccessResponse[CartResponse]:
    cart = await CartService(db).clear_cart(current_user.id)
    return SuccessResponse(message="Cart cleared", data=cart)
