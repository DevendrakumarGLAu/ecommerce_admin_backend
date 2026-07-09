"""Reusable pagination/sorting query-parameter dependency."""

from dataclasses import dataclass
from typing import Literal

from fastapi import Query


@dataclass(slots=True)
class PaginationParams:
    """Common `page`, `limit`, `sort`, `order` query parameters."""

    page: int
    limit: int
    sort: str
    order: Literal["asc", "desc"]

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def get_pagination_params(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    sort: str = Query(default="created_at", description="Field name to sort by"),
    order: Literal["asc", "desc"] = Query(default="desc", description="Sort direction"),
) -> PaginationParams:
    """FastAPI dependency yielding validated pagination parameters."""
    return PaginationParams(page=page, limit=limit, sort=sort, order=order)
