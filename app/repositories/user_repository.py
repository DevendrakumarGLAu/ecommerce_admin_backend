"""Data access for `User` accounts."""

from sqlalchemy import or_, select

from app.dependencies.pagination import PaginationParams
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository

_SORTABLE_FIELDS = frozenset({"first_name", "last_name", "email", "created_at"})


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None

    async def count_all(self) -> int:
        return await self.count()

    async def list_paginated(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        conditions = []
        if search:
            like = f"%{search}%"
            conditions.append(
                or_(User.first_name.ilike(like), User.last_name.ilike(like), User.email.ilike(like))
            )
        if role is not None:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active.is_(is_active))

        sort_column = self.resolve_sort_column(pagination.sort, _SORTABLE_FIELDS)
        order_fn = sort_column.asc() if pagination.order == "asc" else sort_column.desc()

        stmt = select(User).where(*conditions).order_by(order_fn).offset(pagination.offset).limit(pagination.limit)
        items = list((await self.db.execute(stmt)).scalars().all())
        total = await self.count(*conditions)
        return items, total
