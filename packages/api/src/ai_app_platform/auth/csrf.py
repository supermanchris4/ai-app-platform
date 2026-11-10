"""Cross-site request forgery checks for requests made with the session cookie (specs/50-auth.md)."""

import hmac
from urllib.parse import urlsplit

from starlette.requests import Request

from ai_app_platform.auth.context import AccessDeniedError
from ai_app_platform.auth.sessions import AuthSession

STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
CSRF_HEADER = "X-CSRF-Token"


def origin_of(url: str) -> str:
    """The scheme, host and any port of an address, as browsers send them in `Origin`."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}".lower()


def check_csrf(request: Request, session: AuthSession, public_url: str) -> None:
    """A state-changing request needs the session's token and an `Origin` matching the application's address."""
    if request.method not in STATE_CHANGING_METHODS:
        return
    token = request.headers.get(CSRF_HEADER, "")
    origin = request.headers.get("Origin", "")
    if not hmac.compare_digest(token.encode(), session.csrf_token.encode()):
        raise AccessDeniedError("cross-site request forgery token missing or wrong")
    if origin.lower() != origin_of(public_url):
        raise AccessDeniedError("origin does not match the application's address")
