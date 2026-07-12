"""Site-wide settings — a deliberate single-row table."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Settings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Global site configuration. Exactly one row is expected to exist."""

    __tablename__ = "settings"

    site_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hero_banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hero_banner_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hero_banner_subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    support_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(500), nullable=True)
    youtube: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_analytics: Mapped[str | None] = mapped_column(String(100), nullable=True)
    facebook_pixel: Mapped[str | None] = mapped_column(String(100), nullable=True)
