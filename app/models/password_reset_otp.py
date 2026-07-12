"""Password-reset OTP model — short-lived, single-use verification codes."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class PasswordResetOTP(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single OTP issued for one forgot-password attempt.

    Only one row per user is ever "active" (`is_used=False`) at a time —
    requesting a new OTP invalidates any previous unused one for that user
    (see `PasswordResetOTPRepository.invalidate_active_for_user`). The row
    also carries the (separately hashed) short-lived `reset_token` issued
    once the OTP is verified, so the OTP itself can never be replayed to
    reset the password a second time.
    """

    __tablename__ = "password_reset_otps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    reset_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship()
