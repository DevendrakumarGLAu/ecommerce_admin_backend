"""User-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserResponse(BaseModel):
    """Public-facing representation of a user account."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    avatar_url: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Payload for a user updating their own profile (name, phone, avatar)."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=500)


class RoleUpdateRequest(BaseModel):
    """Super-admin-only payload to change another user's role."""

    role: UserRole
