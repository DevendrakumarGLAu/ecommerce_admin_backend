"""Helpers for building the consistent success/error response envelope."""

from typing import Any


def success_payload(data: Any = None, message: str = "Success") -> dict[str, Any]:
    """Build the standard success envelope: {success, message, data}."""
    return {"success": True, "message": message, "data": data}


def error_payload(message: str, errors: Any = None) -> dict[str, Any]:
    """Build the standard error envelope: {success, message, errors}."""
    return {"success": False, "message": message, "errors": errors}
