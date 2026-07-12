"""Business logic for product categories."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.pagination import PaginationParams
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.common import PaginatedData
from app.services import cache_service
from app.utils.exceptions import NotFoundException
from app.utils.slug import build_candidate_slug, generate_slug


class CategoryService:
    """Orchestrates category CRUD, slug generation, and cache invalidation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.categories = CategoryRepository(db)

    async def _generate_unique_slug(self, name: str, exclude_id: uuid.UUID | None = None) -> str:
        base_slug = generate_slug(name)
        attempt = 0
        while True:
            candidate = build_candidate_slug(base_slug, attempt)
            if not await self.categories.slug_exists(candidate, exclude_id=exclude_id):
                return candidate
            attempt += 1

    async def create(self, payload: CategoryCreate) -> Category:
        """Create a category with an auto-generated, unique SEO-friendly slug."""
        slug = await self._generate_unique_slug(payload.name)
        category = await self.categories.create(slug=slug, **payload.model_dump())
        await self.categories.commit()
        await cache_service.invalidate_categories_cache()
        return category

    async def update(self, category_id: uuid.UUID, payload: CategoryUpdate) -> Category:
        """Update a category, regenerating its slug only if `name` changed."""
        category = await self.categories.get_by_id_active(category_id)
        if category is None:
            raise NotFoundException("Category not found")

        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != category.name:
            update_data["slug"] = await self._generate_unique_slug(update_data["name"], exclude_id=category_id)

        category = await self.categories.update(category, **update_data)
        await self.categories.commit()
        await cache_service.invalidate_categories_cache()
        return category

    async def delete(self, category_id: uuid.UUID) -> None:
        """Soft-delete a category."""
        category = await self.categories.get_by_id_active(category_id)
        if category is None:
            raise NotFoundException("Category not found")

        await self.categories.update(category, deleted_at=datetime.now(timezone.utc))
        await self.categories.commit()
        await cache_service.invalidate_categories_cache()

    async def get_by_slug(self, slug: str) -> Category:
        category = await self.categories.get_by_slug(slug)
        if category is None:
            raise NotFoundException("Category not found")
        return category

    async def get_by_id(self, category_id: uuid.UUID) -> Category:
        category = await self.categories.get_by_id_active(category_id)
        if category is None:
            raise NotFoundException("Category not found")
        return category

    async def list_categories(
        self, pagination: PaginationParams, search: str | None, is_active: bool | None = None
    ) -> PaginatedData[CategoryResponse]:
        """List categories with Redis caching, keyed by the full query signature."""
        schema = PaginatedData[CategoryResponse]
        cache_key = cache_service.build_categories_list_key(
            f"{pagination.page}:{pagination.limit}:{pagination.sort}:{pagination.order}:{search or ''}:{is_active}"
        )

        cached = await cache_service.get_cached(cache_key)
        if cached is not None:
            return schema.model_validate(cached)

        items, total = await self.categories.list_paginated(pagination, search, is_active=is_active)
        result = schema.build(
            items=[CategoryResponse.model_validate(item) for item in items],
            page=pagination.page,
            limit=pagination.limit,
            total=total,
        )
        await cache_service.set_cached(cache_key, result.model_dump(mode="json"))
        return result
