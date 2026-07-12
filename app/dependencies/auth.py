"""Authentication and role-based authorization dependencies."""

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import redis_client
from app.core.security import JWTError, TokenType, decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import ForbiddenException, UnauthorizedException

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the `Authorization: Bearer` access token."""
    if credentials is None:
        raise UnauthorizedException("Missing authentication credentials")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedException("Invalid or expired token")

    if payload.get("type") != TokenType.ACCESS.value:
        raise UnauthorizedException("Invalid token type")

    jti = payload.get("jti")
    if jti and await redis_client.get(f"blacklist:{jti}"):
        raise UnauthorizedException("Token has been revoked")

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError:
        raise UnauthorizedException("Invalid token payload")

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedException("User no longer exists")
    if not user.is_active:
        raise UnauthorizedException("User account is deactivated")

    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Like `get_current_user`, but returns None instead of raising when there's no
    (or an invalid) bearer token — for endpoints that behave differently for
    logged-in callers without requiring authentication outright."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except UnauthorizedException:
        return None


def require_roles(*roles: UserRole) -> Callable[[User], Coroutine[Any, Any, User]]:
    """Build a dependency that only allows users with one of the given roles."""

    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException("You do not have permission to perform this action")
        return current_user

    return _dependency


require_admin = require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)
require_super_admin = require_roles(UserRole.SUPER_ADMIN)
