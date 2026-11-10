"""Request logging middleware (specs/20-api-scaffold.md#middleware). Platform module."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


def path_template(request: Request) -> str | None:
    """The template of the route that handled the request, such as `/api/v1/identities/{identity_id}`.

    FastAPI records a route's template relative to the router it was declared on, without the
    prefixes the router was included with. A prefix is fixed text, so it is the part of the path
    before the route's own part, which the route's pattern matches. None when no route matched.
    """
    route = request.scope.get("route")
    route_format: str | None = getattr(route, "path_format", None)
    route_regex = getattr(route, "path_regex", None)
    if route_format is None or route_regex is None:
        return None
    path: str = request.scope["path"]
    for start, character in enumerate(path):
        if character == "/" and route_regex.match(path[start:]):
            return path[:start] + route_format
    return route_format


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every completed request: method, path template, status, duration and actor type.

    The path template (`/api/v1/identities/{identity_id}`) is logged rather than the path, so
    identifiers in URLs are not. The subject is never logged; the audit trail records who acted,
    linked by the correlation ID, which the log formatter adds.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path_template": path_template(request),
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "actor_type": getattr(request.state, "actor_type", None),
            },
        )

        return response
