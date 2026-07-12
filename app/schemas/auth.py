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


class CaptchaResponse(BaseModel):
    captcha_id: str
    svg: str
    expires_in_minutes: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    captcha_id: str = Field(..., min_length=1, description="From a prior GET /auth/captcha call")
    captcha_text: str = Field(..., min_length=1, max_length=12, description="What the user typed from the image")


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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """`otp` is populated only when `settings.OTP_DEBUG_MODE` is on (the default,
    intended for local dev/testing without a real email/SMS provider wired up)."""

    message: str
    expires_in_minutes: int
    otp: str | None = None


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{6}$", description="The 6-digit code from /forgot-password")


class VerifyOtpResponse(BaseModel):
    reset_token: str
    expires_in_minutes: int


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_token: str = Field(..., min_length=1, description="Obtained from a successful /verify-otp call")
    new_password: str = Field(..., min_length=8, max_length=128)
