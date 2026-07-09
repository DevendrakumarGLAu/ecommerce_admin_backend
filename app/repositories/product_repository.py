"""Data access for `Product` records (soft-delete aware) with search/filtering."""

import uuid

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import selectinload

from app.dependencies.filters import ProductFilterParams
from app.dependencies.pagination import PaginationParams
from app.models.category import Category
from app.models.product import Product
from app.repositories.base import BaseRepository

_SORTABLE_FIELDS = frozenset({"title", "price", "created_at", "updated_at", "brand"})


class ProductRepository(BaseRepository[Product]):
    model = Product

    def _base_query(self):
        return select(Product).options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.videos),
            selectinload(Product.marketplace_links),
        )

    def _build_filter_conditions(self, filters: ProductFilterParams) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [Product.deleted_at.is_(None)]

        if filters.category_id is not None:
            conditions.append(Product.category_id == filters.category_id)
        if filters.brand:
            conditions.append(Product.brand.ilike(filters.brand))
        if filters.featured is not None:
            conditions.append(Product.featured.is_(filters.featured))
        if filters.bestseller is not None:
            conditions.append(Product.bestseller.is_(filters.bestseller))
        if filters.new_arrival is not None:
            conditions.append(Product.new_arrival.is_(filters.new_arrival))
        if filters.stock_status is not None:
            conditions.append(Product.stock_status == filters.stock_status)
        if filters.status is not None:
            conditions.append(Product.status == filters.status)
        if filters.price_min is not None:
            conditions.append(Product.price >= filters.price_min)
        if filters.price_max is not None:
            conditions.append(Product.price <= filters.price_max)

        return conditions

    async def get_by_id_active(self, id_: uuid.UUID) -> Product | None:
        stmt = self._base_query().where(Product.id == id_, Product.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        stmt = self._base_query().where(Product.slug == slug, Product.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(Product.id).where(Product.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Product.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def sku_exists(self, sku: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(Product.id).where(Product.sku == sku)
        if exclude_id is not None:
            stmt = stmt.where(Product.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_paginated(
        self, pagination: PaginationParams, filters: ProductFilterParams
    ) -> tuple[list[Product], int]:
        conditions = self._build_filter_conditions(filters)

        stmt = self._base_query()
        if filters.category_slug:
            stmt = stmt.join(Category, Product.category_id == Category.id).where(Category.slug == filters.category_slug)

        if filters.search:
            like = f"%{filters.search}%"
            search_condition = or_(
                Product.title.ilike(like),
                Product.brand.ilike(like),
                Product.category.has(Category.name.ilike(like)),
            )
            conditions.append(search_condition)

        sort_column = self.resolve_sort_column(pagination.sort, _SORTABLE_FIELDS)
        order_fn = sort_column.asc() if pagination.order == "asc" else sort_column.desc()

        stmt = stmt.where(*conditions).order_by(order_fn).offset(pagination.offset).limit(pagination.limit)
        items = list((await self.db.execute(stmt)).unique().scalars().all())

        count_stmt = select(func.count(Product.id.distinct())).select_from(Product).where(*conditions)
        if filters.category_slug:
            count_stmt = count_stmt.join(Category, Product.category_id == Category.id).where(
                Category.slug == filters.category_slug
            )
        total = (await self.db.execute(count_stmt)).scalar_one()

        return items, total

    async def list_featured(self, limit: int) -> list[Product]:
        stmt = (
            self._base_query()
            .where(Product.deleted_at.is_(None), Product.featured.is_(True))
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        return list((await self.db.execute(stmt)).unique().scalars().all())

    async def list_recent(self, limit: int) -> list[Product]:
        stmt = self._base_query().where(Product.deleted_at.is_(None)).order_by(Product.created_at.desc()).limit(limit)
        return list((await self.db.execute(stmt)).unique().scalars().all())

    async def count_active(self) -> int:
        return await self.count(Product.deleted_at.is_(None))
