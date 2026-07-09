"""Global exception handlers producing the consistent success/error JSON envelope."""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.utils.exceptions import AppException
from app.utils.response import error_payload

logger = get_logger("app.errors")


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI app."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Handled application exception",
            extra={"path": request.url.path, "status_code": exc.status_code, "error_message": exc.message},
        )
        return JSONResponse(status_code=exc.status_code, content=error_payload(exc.message, exc.errors))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = jsonable_encoder(exc.errors())
        logger.warning("Request validation failed", extra={"path": request.url.path, "validation_errors": errors})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_payload("Validation error", errors),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            logger.warning("Authentication failure", extra={"path": request.url.path})
        return JSONResponse(status_code=exc.status_code, content=error_payload(str(exc.detail)))

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload("Internal server error"),
        )
