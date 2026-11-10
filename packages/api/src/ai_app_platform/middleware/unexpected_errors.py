"""Unexpected error middleware (specs/20-api-scaffold.md#middleware). Platform module."""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

ErrorHandler = Callable[[Request, Exception], Awaitable[Response]]


class UnexpectedErrorMiddleware(BaseHTTPMiddleware):
    """Turns an exception no exception handler took into the application's error response.

    Starlette handles such an exception outside every middleware, after the correlation ID's
    context has ended, so it would be logged without the ID, the request would not be logged, and
    the response would lack the ID headers. Added first, so it runs inside the other middleware,
    this calls the handler while the request's context is still in place.
    """

    def __init__(self, app: ASGIApp, handler: ErrorHandler) -> None:
        super().__init__(app)
        self._handler = handler

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001  # every unexpected error becomes the 500 response
            return await self._handler(request, exc)
