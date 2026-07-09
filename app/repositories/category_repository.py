"""Data access for `Category` records (soft-delete aware)."""

import uuid

from sqlalchemy import or_, select

from app.dependencies.pagination import PaginationParams
from app.models.category import Category
from app.repositories.base import BaseRepository

_SORTABLE_FIELDS = frozenset({"name", "created_at", "updated_at"})


class CategoryRepository(BaseRepository[Category]):
    model = Category

    async def get_by_id_active(self, id_: uuid.UUID) -> Category | None:
        instance = await self.get_by_id(id_)
        return instance if instance and not instance.is_deleted else None

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug, Category.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(Category.id).where(Category.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_paginated(self, pagination: PaginationParams, search: str | None) -> tuple[list[Category], int]:
        conditions = [Category.deleted_at.is_(None)]
        if search:
            conditions.append(or_(Category.name.ilike(f"%{search}%"), Category.description.ilike(f"%{search}%")))

        sort_column = self.resolve_sort_column(pagination.sort, _SORTABLE_FIELDS)
        order_fn = sort_column.asc() if pagination.order == "asc" else sort_column.desc()

        stmt = select(Category).where(*conditions).order_by(order_fn).offset(pagination.offset).limit(pagination.limit)
        items = list((await self.db.execute(stmt)).scalars().all())
        total = await self.count(*conditions)
        return items, total
