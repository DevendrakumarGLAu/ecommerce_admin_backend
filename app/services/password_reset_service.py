"""Business logic for the OTP-based forgot-password flow.

Flow:
1. `POST /auth/forgot-password` — look up the user, invalidate any OTP still
   outstanding for them, generate a cryptographically random 6-digit OTP,
   store only its bcrypt hash with a 5-minute expiry, hand it to
   `otp_notifier.send_otp` (logs today; swap that module for real email/SMS
   later — nothing here changes), and — only when `settings.OTP_DEBUG_MODE`
   is on — also return it in the response for local testing.
2. `POST /auth/verify-otp` — fetch the user's active OTP row, reject it if
   expired or already locked out from too many wrong attempts, compare the
   submitted code against the stored hash. On success, mark the row verified
   and issue a second, unrelated secret — a short-lived `reset_token` — so
   the OTP itself is never reusable to change the password more than once.
3. `POST /auth/reset-password` — require a verified, unexpired OTP row whose
   `reset_token` hash matches the one supplied, hash the new password with
   the same bcrypt helper used everywhere else in the app, update the user,
   and mark the OTP row used so neither the OTP nor the reset token can ever
   be replayed.
"""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.password_reset_otp import PasswordResetOTP
from app.repositories.password_reset_otp_repository import PasswordResetOTPRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ForgotPasswordResponse, VerifyOtpResponse
from app.services.otp_notifier import send_otp
from app.utils.exceptions import BadRequestException, NotFoundException, RateLimitExceededException

_OTP_LENGTH = 6


class PasswordResetService:
    """Orchestrates the request-OTP / verify-OTP / reset-password lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.otps = PasswordResetOTPRepository(db)

    @staticmethod
    def _generate_otp() -> str:
        """Cryptographically secure 6-digit numeric code (leading zeros allowed,
        so the full 1,000,000-value space is used, not just 100000-999999)."""
        return f"{secrets.randbelow(10 ** _OTP_LENGTH):0{_OTP_LENGTH}d}"

    async def request_reset(self, email: str) -> ForgotPasswordResponse:
        user = await self.users.get_by_email(email)
        if user is None:
            raise NotFoundException("No account found with that email address")

        # A fresh request always supersedes whatever OTP was issued before it.
        await self.otps.invalidate_active_for_user(user.id)

        otp = self._generate_otp()
        now = datetime.now(timezone.utc)
        await self.otps.create(
            user_id=user.id,
            otp_hash=hash_password(otp),
            expires_at=now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
        )
        await self.otps.commit()

        # The one seam for a real email/SMS provider — see otp_notifier.py.
        await send_otp(user, otp, settings.OTP_EXPIRY_MINUTES)

        return ForgotPasswordResponse(
            message="An OTP has been generated for your account.",
            expires_in_minutes=settings.OTP_EXPIRY_MINUTES,
            otp=otp if settings.OTP_DEBUG_MODE else None,
        )

    async def verify_otp(self, email: str, otp: str) -> VerifyOtpResponse:
        user = await self.users.get_by_email(email)
        if user is None:
            raise NotFoundException("No account found with that email address")

        record = await self.otps.get_active_for_user(user.id)
        if record is None:
            raise BadRequestException("No active OTP found. Please request a new one.")

        now = datetime.now(timezone.utc)
        if self._is_expired(record.expires_at, now):
            await self._invalidate(record)
            raise BadRequestException("This OTP has expired. Please request a new one.")

        if record.attempts >= settings.OTP_MAX_ATTEMPTS:
            await self._invalidate(record)
            raise RateLimitExceededException("Too many incorrect attempts. Please request a new OTP.")

        if not verify_password(otp, record.otp_hash):
            record.attempts += 1
            await self.otps.commit()
            remaining = settings.OTP_MAX_ATTEMPTS - record.attempts
            raise BadRequestException(f"Incorrect OTP. {remaining} attempt(s) remaining.")

        reset_token = secrets.token_urlsafe(32)
        record.is_verified = True
        record.reset_token_hash = hash_password(reset_token)
        record.reset_token_expires_at = now + timedelta(minutes=settings.OTP_RESET_TOKEN_EXPIRY_MINUTES)
        await self.otps.commit()

        return VerifyOtpResponse(
            reset_token=reset_token, expires_in_minutes=settings.OTP_RESET_TOKEN_EXPIRY_MINUTES
        )

    async def reset_password(self, email: str, reset_token: str, new_password: str) -> None:
        user = await self.users.get_by_email(email)
        if user is None:
            raise NotFoundException("No account found with that email address")

        record = await self.otps.get_active_for_user(user.id)
        if record is None or not record.is_verified or record.reset_token_hash is None:
            raise BadRequestException("OTP verification is required before resetting the password.")

        now = datetime.now(timezone.utc)
        if record.reset_token_expires_at is None or self._is_expired(record.reset_token_expires_at, now):
            await self._invalidate(record)
            raise BadRequestException("Your verification has expired. Please restart the password reset process.")

        if not verify_password(reset_token, record.reset_token_hash):
            raise BadRequestException("Invalid reset token.")

        await self.users.update(user, password_hash=hash_password(new_password))
        record.is_used = True
        await self.otps.commit()

    @staticmethod
    def _is_expired(expires_at: datetime, now: datetime) -> bool:
        return expires_at <= now

    async def _invalidate(self, record: PasswordResetOTP) -> None:
        record.is_used = True
        await self.otps.commit()
