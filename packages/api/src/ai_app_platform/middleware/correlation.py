"""Correlation ID middleware for request tracing (specs/20-api-scaffold.md#middleware). Platform module."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from ai_app_platform.logging_config import correlation_id_var, request_id_var


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation and request IDs.

    - Reads X-Correlation-ID from request header, or generates UUID if absent
    - Generates unique X-Request-ID for each request
    - Stores both in request state for access in routes, and in context variables for logging
    - Echoes both in response headers
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        correlation_token = correlation_id_var.set(correlation_id)
        request_token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
        finally:
            correlation_id_var.reset(correlation_token)
            request_id_var.reset(request_token)

        # Echo in response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id

        return response
