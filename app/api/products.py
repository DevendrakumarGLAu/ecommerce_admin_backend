"""Product endpoints — public reads with search/filter/sort, admin-only writes."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.dependencies.filters import ProductFilterParams, get_product_filter_params
from app.dependencies.pagination import PaginationParams, get_pagination_params
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.product import (
    MarketplaceLinkCreate,
    MarketplaceLinkResponse,
    ProductCreate,
    ProductImageCreate,
    ProductImageResponse,
    ProductResponse,
    ProductSummaryResponse,
    ProductUpdate,
    ProductVideoCreate,
    ProductVideoResponse,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=SuccessResponse[PaginatedData[ProductSummaryResponse]],
    summary="List products",
    description=(
        "Paginated, sortable list of products. Supports search by title/brand/category and filters "
        "for category, brand, featured, bestseller, new_arrival, price range, and stock status."
    ),
)
async def list_products(
    filters: ProductFilterParams = Depends(get_product_filter_params),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[PaginatedData[ProductSummaryResponse]]:
    result = await ProductService(db).list_products(pagination, filters)
    return SuccessResponse(data=result)


@router.get(
    "/{slug}",
    response_model=SuccessResponse[ProductResponse],
    summary="Get a product by slug",
    description="Returns the full product detail, including its category and images, by slug.",
)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)) -> SuccessResponse[ProductResponse]:
    product = await ProductService(db).get_by_slug(slug)
    return SuccessResponse(data=ProductResponse.model_validate(product))


@router.post(
    "",
    response_model=SuccessResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a product (admin only)",
    description="Creates a product. A unique, SEO-friendly slug is generated automatically from `title`.",
    dependencies=[Depends(require_admin)],
)
async def create_product(
    payload: ProductCreate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[ProductResponse]:
    product = await ProductService(db).create(payload)
    return SuccessResponse(message="Product created", data=ProductResponse.model_validate(product))


@router.put(
    "/{product_id}",
    response_model=SuccessResponse[ProductResponse],
    summary="Update a product (admin only)",
    description="Partially updates a product. The slug is regenerated only if `title` changes.",
    dependencies=[Depends(require_admin)],
)
async def update_product(
    product_id: uuid.UUID, payload: ProductUpdate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[ProductResponse]:
    product = await ProductService(db).update(product_id, payload)
    return SuccessResponse(message="Product updated", data=ProductResponse.model_validate(product))


@router.delete(
    "/{product_id}",
    response_model=SuccessResponse[None],
    summary="Delete a product (admin only)",
    description="Soft-deletes a product so it is excluded from all listings while preserving history.",
    dependencies=[Depends(require_admin)],
)
async def delete_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SuccessResponse[None]:
    await ProductService(db).delete(product_id)
    return SuccessResponse(message="Product deleted")


@router.post(
    "/{product_id}/images",
    response_model=SuccessResponse[ProductImageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Attach an image to a product (admin only)",
    description="Associates an already-uploaded image URL (see POST /uploads/image) with a product.",
    dependencies=[Depends(require_admin)],
)
async def add_product_image(
    product_id: uuid.UUID, payload: ProductImageCreate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[ProductImageResponse]:
    image = await ProductService(db).add_image(product_id, payload)
    return SuccessResponse(message="Image attached", data=ProductImageResponse.model_validate(image))


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=SuccessResponse[None],
    summary="Remove an image from a product (admin only)",
    description="Deletes the product-image association and removes the corresponding file from Supabase Storage.",
    dependencies=[Depends(require_admin)],
)
async def remove_product_image(
    product_id: uuid.UUID, image_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    await ProductService(db).remove_image(product_id, image_id)
    return SuccessResponse(message="Image removed")


@router.post(
    "/{product_id}/videos",
    response_model=SuccessResponse[ProductVideoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Attach a video to a product (admin only)",
    description="Associates an already-uploaded video URL (see POST /uploads/video) with a product.",
    dependencies=[Depends(require_admin)],
)
async def add_product_video(
    product_id: uuid.UUID, payload: ProductVideoCreate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[ProductVideoResponse]:
    video = await ProductService(db).add_video(product_id, payload)
    return SuccessResponse(message="Video attached", data=ProductVideoResponse.model_validate(video))


@router.delete(
    "/{product_id}/videos/{video_id}",
    response_model=SuccessResponse[None],
    summary="Remove a video from a product (admin only)",
    description="Deletes the product-video association and removes the corresponding file from Supabase Storage.",
    dependencies=[Depends(require_admin)],
)
async def remove_product_video(
    product_id: uuid.UUID, video_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    await ProductService(db).remove_video(product_id, video_id)
    return SuccessResponse(message="Video removed")


@router.post(
    "/{product_id}/marketplace-links",
    response_model=SuccessResponse[MarketplaceLinkResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Attach a marketplace buy link to a product (admin only)",
    description="Adds a 'buy it here' link for a marketplace (Amazon, Flipkart, Meesho, Myntra, Snapdeal, or other).",
    dependencies=[Depends(require_admin)],
)
async def add_marketplace_link(
    product_id: uuid.UUID, payload: MarketplaceLinkCreate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[MarketplaceLinkResponse]:
    link = await ProductService(db).add_marketplace_link(product_id, payload)
    return SuccessResponse(message="Marketplace link added", data=MarketplaceLinkResponse.model_validate(link))


@router.delete(
    "/{product_id}/marketplace-links/{link_id}",
    response_model=SuccessResponse[None],
    summary="Remove a marketplace buy link from a product (admin only)",
    description="Deletes a previously attached marketplace link.",
    dependencies=[Depends(require_admin)],
)
async def remove_marketplace_link(
    product_id: uuid.UUID, link_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    await ProductService(db).remove_marketplace_link(product_id, link_id)
    return SuccessResponse(message="Marketplace link removed")
