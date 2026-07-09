"""Redis-backed fixed-window rate limiting middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.redis import redis_client
from app.utils.response import error_payload

_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limits each client IP+path to `RATE_LIMIT_PER_MINUTE` requests per rolling minute."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{request.url.path}"

        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, _WINDOW_SECONDS)

        if current > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content=error_payload("Too many requests, please try again later"),
            )

        return await call_next(request)
