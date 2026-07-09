"""Query-parameter dependency for the admin user listing endpoint."""

from dataclasses import dataclass

from fastapi import Query

from app.models.user import UserRole


@dataclass(slots=True)
class UserFilterParams:
    """Optional filters accepted by the user listing endpoint."""

    search: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


def get_user_filter_params(
    search: str | None = Query(default=None, description="Search by first name, last name, or email"),
    role: UserRole | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
) -> UserFilterParams:
    """FastAPI dependency yielding validated user filter parameters."""
    return UserFilterParams(search=search, role=role, is_active=is_active)
