"""The error response shape and the platform's error handlers (specs/20-api-scaffold.md#errors).

Every error response is `{"error": {code, message, details, correlation_id, request_id}}`. The
platform handles the errors it raises (authentication, access, request validation) and unexpected
ones; an application adds handlers for its own errors with `error_body`.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ai_app_platform.auth.context import AccessDeniedError, AuthenticationError

logger = logging.getLogger(__name__)


def error_body(
    request: Request,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """The error response body, carrying the request's correlation and request IDs."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "correlation_id": getattr(request.state, "correlation_id", None),
            "request_id": getattr(request.state, "request_id", None),
        }
    }


async def authentication_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """No valid token or session. The response never says which check failed."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_body(request, "UNAUTHORIZED", "Authentication required"),
    )


async def access_denied_handler(request: Request, exc: Exception) -> JSONResponse:
    """A missing role or failed cross-site request forgery check. The response never says which."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_body(request, "FORBIDDEN", "Not permitted"),
    )


async def request_validation_handler(request: Request, exc: Exception) -> JSONResponse:
    """A request that does not match its schema."""
    assert isinstance(exc, RequestValidationError)
    details: list[dict[str, Any]] = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({"field": field, "issue": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_body(request, "VALIDATION_ERROR", "Request validation failed", details),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """An unexpected error: logged with the request's IDs, never with its message, and a 500."""
    logger.exception("Unexpected error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_body(request, "INTERNAL_ERROR", "An unexpected error occurred"),
    )


def install_error_handlers(app: FastAPI) -> None:
    """Register the platform's error handlers on the application."""
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(AccessDeniedError, access_denied_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(Exception, general_exception_handler)
