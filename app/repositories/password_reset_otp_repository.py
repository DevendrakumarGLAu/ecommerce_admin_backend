"""Data access for password-reset OTP records."""

import uuid

from sqlalchemy import select

from app.models.password_reset_otp import PasswordResetOTP
from app.repositories.base import BaseRepository


class PasswordResetOTPRepository(BaseRepository[PasswordResetOTP]):
    model = PasswordResetOTP

    async def get_active_for_user(self, user_id: uuid.UUID) -> PasswordResetOTP | None:
        """The most recent not-yet-used OTP for a user (may or may not be expired —
        callers check `expires_at`/`reset_token_expires_at` themselves so they can
        return a specific "expired" error rather than a generic "not found")."""
        stmt = (
            select(PasswordResetOTP)
            .where(PasswordResetOTP.user_id == user_id, PasswordResetOTP.is_used.is_(False))
            .order_by(PasswordResetOTP.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def invalidate_active_for_user(self, user_id: uuid.UUID) -> None:
        """Mark every unused OTP for a user as used, so a fresh request always
        supersedes whatever was issued before it."""
        stmt = select(PasswordResetOTP).where(
            PasswordResetOTP.user_id == user_id, PasswordResetOTP.is_used.is_(False)
        )
        result = await self.db.execute(stmt)
        for otp in result.scalars().all():
            otp.is_used = True
        await self.db.flush()
