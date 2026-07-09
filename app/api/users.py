"""Admin user management endpoints: list, view, activate/deactivate."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.dependencies.pagination import PaginationParams, get_pagination_params
from app.dependencies.user_filters import UserFilterParams, get_user_filter_params
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.user import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_admin)])


@router.get(
    "",
    response_model=SuccessResponse[PaginatedData[UserResponse]],
    summary="List users (admin only)",
    description="Paginated, sortable list of users. Supports search by name/email and filters by role/active status.",
)
async def list_users(
    filters: UserFilterParams = Depends(get_user_filter_params),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[PaginatedData[UserResponse]]:
    result = await UserService(db).list_users(pagination, filters)
    return SuccessResponse(data=result)


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    summary="Get a user by id (admin only)",
    description="Returns a single user's profile.",
)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SuccessResponse[UserResponse]:
    user = await UserService(db).get_by_id(user_id)
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.patch(
    "/{user_id}/activate",
    response_model=SuccessResponse[UserResponse],
    summary="Activate a user (admin only)",
    description="Re-enables a deactivated user's ability to authenticate.",
)
async def activate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SuccessResponse[UserResponse]:
    user = await UserService(db).set_active(user_id, True)
    return SuccessResponse(message="User activated", data=UserResponse.model_validate(user))


@router.patch(
    "/{user_id}/deactivate",
    response_model=SuccessResponse[UserResponse],
    summary="Deactivate a user (admin only)",
    description="Prevents the user from authenticating without deleting their account.",
)
async def deactivate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SuccessResponse[UserResponse]:
    user = await UserService(db).set_active(user_id, False)
    return SuccessResponse(message="User deactivated", data=UserResponse.model_validate(user))
