"""Site settings request/response schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SettingsUpdate(BaseModel):
    """Admin-only payload; all fields optional (PATCH semantics)."""

    site_name: str | None = Field(default=None, max_length=150)
    logo: str | None = Field(default=None, max_length=500)
    favicon: str | None = Field(default=None, max_length=500)
    support_email: EmailStr | None = None
    support_phone: str | None = Field(default=None, max_length=20)
    facebook: str | None = Field(default=None, max_length=500)
    instagram: str | None = Field(default=None, max_length=500)
    youtube: str | None = Field(default=None, max_length=500)
    twitter: str | None = Field(default=None, max_length=500)
    google_analytics: str | None = Field(default=None, max_length=100)
    facebook_pixel: str | None = Field(default=None, max_length=100)


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_name: str | None
    logo: str | None
    favicon: str | None
    support_email: str | None
    support_phone: str | None
    facebook: str | None
    instagram: str | None
    youtube: str | None
    twitter: str | None
    google_analytics: str | None
    facebook_pixel: str | None
