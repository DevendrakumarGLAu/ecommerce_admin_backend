"""Wishlist endpoints — authenticated users manage their own wishlist."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.wishlist import WishlistCreate, WishlistResponse
from app.services.wishlist_service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get(
    "",
    response_model=SuccessResponse[list[WishlistResponse]],
    summary="List wishlist items",
    description="Returns all products the authenticated user has wishlisted.",
)
async def list_wishlist(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SuccessResponse[list[WishlistResponse]]:
    items = await WishlistService(db).list_for_user(current_user.id)
    return SuccessResponse(data=items)


@router.post(
    "",
    response_model=SuccessResponse[WishlistResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a product to the wishlist",
    description="Adds a product to the authenticated user's wishlist.",
)
async def add_to_wishlist(
    payload: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[WishlistResponse]:
    entry = await WishlistService(db).add(current_user.id, payload.product_id)
    return SuccessResponse(message="Product added to wishlist", data=entry)


@router.delete(
    "/{product_id}",
    response_model=SuccessResponse[None],
    summary="Remove a product from the wishlist",
    description="Removes a product from the authenticated user's wishlist.",
)
async def remove_from_wishlist(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[None]:
    await WishlistService(db).remove(current_user.id, product_id)
    return SuccessResponse(message="Product removed from wishlist")
