"""Category endpoints — public reads, admin-only writes."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.dependencies.pagination import PaginationParams, get_pagination_params
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.common import PaginatedData, SuccessResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=SuccessResponse[PaginatedData[CategoryResponse]],
    summary="List categories",
    description="Paginated, sortable list of categories with optional search by name/description.",
)
async def list_categories(
    search: str | None = Query(default=None, description="Search by category name or description"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[PaginatedData[CategoryResponse]]:
    result = await CategoryService(db).list_categories(pagination, search)
    return SuccessResponse(data=result)


@router.get(
    "/{slug}",
    response_model=SuccessResponse[CategoryResponse],
    summary="Get a category by slug",
    description="Returns a single category identified by its SEO-friendly slug.",
)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)) -> SuccessResponse[CategoryResponse]:
    category = await CategoryService(db).get_by_slug(slug)
    return SuccessResponse(data=CategoryResponse.model_validate(category))


@router.post(
    "",
    response_model=SuccessResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a category (admin only)",
    description="Creates a category. A unique, SEO-friendly slug is generated automatically from `name`.",
    dependencies=[Depends(require_admin)],
)
async def create_category(
    payload: CategoryCreate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[CategoryResponse]:
    category = await CategoryService(db).create(payload)
    return SuccessResponse(message="Category created", data=CategoryResponse.model_validate(category))


@router.put(
    "/{category_id}",
    response_model=SuccessResponse[CategoryResponse],
    summary="Update a category (admin only)",
    description="Partially updates a category. The slug is regenerated only if `name` changes.",
    dependencies=[Depends(require_admin)],
)
async def update_category(
    category_id: uuid.UUID, payload: CategoryUpdate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[CategoryResponse]:
    category = await CategoryService(db).update(category_id, payload)
    return SuccessResponse(message="Category updated", data=CategoryResponse.model_validate(category))


@router.delete(
    "/{category_id}",
    response_model=SuccessResponse[None],
    summary="Delete a category (admin only)",
    description="Soft-deletes a category so it is excluded from all listings while preserving history.",
    dependencies=[Depends(require_admin)],
)
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SuccessResponse[None]:
    await CategoryService(db).delete(category_id)
    return SuccessResponse(message="Category deleted")
