"""Application-level exception hierarchy.

Service and repository code raises these instead of HTTPException so that
business logic stays framework-agnostic. Handlers registered in
`app.middleware.error_handler` translate them into the consistent JSON
envelope used across the API.
"""

from typing import Any

from starlette import status


class AppException(Exception):
    """Base class for all handled application exceptions."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None, errors: Any = None) -> None:
        self.message = message or self.default_message
        self.errors = errors
        super().__init__(self.message)


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Resource not found"


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Resource already exists"


class BadRequestException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Invalid request"


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Authentication required"


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You do not have permission to perform this action"


class UnprocessableEntityException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_message = "Unable to process request"


class RateLimitExceededException(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_message = "Too many requests, please try again later"
