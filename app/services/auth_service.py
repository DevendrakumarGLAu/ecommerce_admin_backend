"""Business logic for authentication: register, login, refresh, logout, password change."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.core.security import (
    JWTError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import ProfileUpdateRequest
from app.services import captcha_service
from app.utils.exceptions import BadRequestException, ConflictException, UnauthorizedException


class AuthService:
    """Orchestrates user registration and the JWT access/refresh token lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def register(self, payload: RegisterRequest) -> User:
        """Create a new customer account. Raises `ConflictException` on duplicate email."""
        if await self.users.email_exists(payload.email):
            raise ConflictException("An account with this email already exists")

        user = await self.users.create(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
            password_hash=hash_password(payload.password),
        )
        await self.users.commit()
        return user

    async def register_admin(self, payload: RegisterRequest) -> TokenResponse:
        """Create a new admin account and immediately issue a token pair (signup + auto-login).

        Used only by the admin panel's signup screen — the public buyer-facing
        `register()` above always creates a customer account and never touches
        this. There's no invite/approval step yet; anyone with access to the
        admin panel's signup form can create an admin account.
        """
        if await self.users.email_exists(payload.email):
            raise ConflictException("An account with this email already exists")

        user = await self.users.create(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
            password_hash=hash_password(payload.password),
            role=UserRole.ADMIN,
        )
        await self.users.commit()
        return self._issue_tokens(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Verify the captcha, then validate credentials and issue a fresh token pair.

        Captcha is checked first: it's single-use and cheap (no DB hit), so a
        bad captcha never wastes a lookup against the users table, and — same
        as a bad password — never reveals whether the email exists.
        """
        await captcha_service.verify(payload.captcha_id, payload.captcha_text)

        user = await self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException("Your account has been deactivated")

        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id))
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Exchange a valid, non-revoked refresh token for a new token pair (rotation)."""
        payload = self._decode_refresh_token(refresh_token)

        try:
            user_id = uuid.UUID(payload.get("sub", ""))
        except ValueError:
            raise UnauthorizedException("Invalid token payload")

        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        await self._blacklist_token(payload)
        return self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token so it can no longer be used to mint access tokens."""
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            return
        await self._blacklist_token(payload)

    def _decode_refresh_token(self, refresh_token: str) -> dict[str, Any]:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedException("Invalid or expired refresh token")

        if payload.get("type") != TokenType.REFRESH.value:
            raise UnauthorizedException("Invalid token type")
        return payload

    async def _blacklist_token(self, payload: dict[str, Any]) -> None:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await redis_client.set(f"blacklist:{jti}", "1", ex=ttl)

    async def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        """Verify the current password and persist a new bcrypt hash."""
        if not verify_password(payload.current_password, user.password_hash):
            raise BadRequestException("Current password is incorrect")

        await self.users.update(user, password_hash=hash_password(payload.new_password))
        await self.users.commit()

    async def update_profile(self, user: User, payload: ProfileUpdateRequest) -> User:
        """Update the caller's own name/phone/avatar. Email and role are not self-editable."""
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return user
        user = await self.users.update(user, **update_data)
        await self.users.commit()
        return user
