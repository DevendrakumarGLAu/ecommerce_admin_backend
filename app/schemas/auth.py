"""Authentication request/response schemas."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

_PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


class RegisterRequest(BaseModel):
    """Payload for creating a new customer account."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(..., min_length=8, max_length=128, description="Must be at least 8 characters")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is not None and not _PHONE_PATTERN.match(value):
            raise ValueError("Invalid phone number format")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
