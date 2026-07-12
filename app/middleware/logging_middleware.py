"""Structured, per-request access logging middleware."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one structured JSON entry per request: method, path, status, duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "Unhandled exception while processing request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            from app.core.config import settings
            from app.middleware.error_handler import CORSResponse
            from app.utils.response import error_payload
            import traceback

            if settings.DEBUG:
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                return CORSResponse(
                    request,
                    status_code=500,
                    content=error_payload(
                        message=f"Internal Server Error: {str(exc)}",
                        errors={"traceback": tb, "exception_type": type(exc).__name__}
                    ),
                )
            return CORSResponse(
                request,
                status_code=500,
                content=error_payload("Internal server error"),
            )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log = logger.warning if response.status_code >= 400 else logger.info
        log(
            "Request handled",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
