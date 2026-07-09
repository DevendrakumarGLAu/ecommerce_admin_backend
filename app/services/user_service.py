"""Business logic for admin user management: list, view, activate/deactivate."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.pagination import PaginationParams
from app.dependencies.user_filters import UserFilterParams
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedData
from app.schemas.user import UserResponse
from app.utils.exceptions import NotFoundException


class UserService:
    """Orchestrates admin-facing user listing and activation toggling."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        return user

    async def list_users(
        self, pagination: PaginationParams, filters: UserFilterParams
    ) -> PaginatedData[UserResponse]:
        schema = PaginatedData[UserResponse]
        items, total = await self.users.list_paginated(
            pagination, search=filters.search, role=filters.role, is_active=filters.is_active
        )
        return schema.build(
            items=[UserResponse.model_validate(item) for item in items],
            page=pagination.page,
            limit=pagination.limit,
            total=total,
        )

    async def set_active(self, user_id: uuid.UUID, is_active: bool) -> User:
        user = await self.get_by_id(user_id)
        user = await self.users.update(user, is_active=is_active)
        await self.users.commit()
        return user
