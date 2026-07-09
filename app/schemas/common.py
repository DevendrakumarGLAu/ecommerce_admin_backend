"""Generic response envelopes shared by every endpoint."""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    """Standard success envelope returned by (almost) every endpoint."""

    success: bool = True
    message: str = "Success"
    data: DataT | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope returned by exception handlers."""

    success: bool = False
    message: str
    errors: object | None = None


class PaginatedData(BaseModel, Generic[DataT]):
    """Payload shape for any paginated listing endpoint."""

    model_config = ConfigDict(from_attributes=True)

    items: list[DataT]
    page: int
    limit: int
    total: int
    pages: int

    @classmethod
    def build(cls, items: list[DataT], page: int, limit: int, total: int) -> "PaginatedData[DataT]":
        pages = math.ceil(total / limit) if limit else 0
        return cls(items=items, page=page, limit=limit, total=total, pages=pages)
