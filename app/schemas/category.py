"""Category request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    seo_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)
    meta_keywords: str | None = Field(default=None, max_length=500)


class CategoryCreate(CategoryBase):
    """Admin payload to create a category. Slug is derived from `name`."""


class CategoryUpdate(BaseModel):
    """Admin payload to update a category. All fields optional (PATCH semantics)."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    image: str | None = Field(default=None, max_length=500)
    description: str | None = None
    seo_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)
    meta_keywords: str | None = Field(default=None, max_length=500)


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime
