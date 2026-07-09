"""Generic async repository providing common single-entity CRUD operations.

Domain repositories subclass this for entity-specific queries. Repositories
never commit the transaction themselves (except explicit `commit()`); the
service layer owns transaction boundaries so multiple repository calls can
participate in a single unit of work.
"""

import uuid
from typing import Any, ClassVar, Generic, TypeVar

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base data-access class wrapping common operations for a single model."""

    model: ClassVar[type[Any]]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id_: uuid.UUID) -> ModelType | None:
        """Fetch a single row by primary key, or None if it doesn't exist."""
        return await self.db.get(self.model, id_)

    async def create(self, **kwargs: Any) -> ModelType:
        """Insert a new row and return the refreshed instance."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs: Any) -> ModelType:
        """Apply attribute updates to an existing instance and flush them."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Hard-delete a row."""
        await self.db.delete(instance)
        await self.db.flush()

    async def count(self, *filters: ColumnElement[bool]) -> int:
        """Count rows matching the given filter predicates."""
        stmt = select(func.count()).select_from(self.model).where(*filters)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.db.commit()

    def resolve_sort_column(self, sort: str, allowed_fields: frozenset[str], default: str = "created_at") -> ColumnElement[Any]:
        """Map a validated `sort` query value to an actual model column."""
        field = sort if sort in allowed_fields else default
        return getattr(self.model, field)
