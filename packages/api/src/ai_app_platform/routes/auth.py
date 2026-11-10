"""Sign-in endpoints under /api/auth/ (specs/20-api-scaffold.md#authentication-and-authorisation).

Platform module. Unversioned, because they are part of the platform rather than the business API.
"""

import html
import logging
from collections.abc import Generator
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from ai_app_platform.auth.context import AuthenticationError
from ai_app_platform.auth.csrf import check_csrf, origin_of
from ai_app_platform.auth.providers import get_providers
from ai_app_platform.auth.sessions import (
    SESSION_COOKIE,
    AuthSession,
    create_session,
    delete_session,
    find_active_session,
)
from ai_app_platform.auth.web_sign_in import (
    CALLBACK_PATH,
    FLOW_COOKIE,
    FLOW_COOKIE_MAX_AGE_SECONDS,
    SignInFlow,
    finish_sign_in,
    is_safe_return_path,
    sign_out_address,
    start_sign_in,
)
from ai_app_platform.config import platform_settings
from ai_app_platform.dependencies import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Sign-in"])


def get_http_client() -> Generator[httpx.Client]:
    """The HTTP client for the token endpoint; tests override it."""
    with httpx.Client(timeout=10) as client:
        yield client


HttpClient = Annotated[httpx.Client, Depends(get_http_client)]


class SessionResponse(BaseModel):
    display_name: str | None
    actor_type: str
    roles: list[str]
    csrf_token: str


class LogoutResponse(BaseModel):
    logout_url: str | None


def _redirect_uri() -> str:
    return origin_of(str(platform_settings().app_public_url)) + CALLBACK_PATH


def _set_cookie(response: JSONResponse | RedirectResponse, name: str, value: str, max_age: int) -> None:
    # __Host- cookies must be Secure, have Path=/ and no Domain. Browsers treat http://localhost as secure.
    response.set_cookie(name, value, max_age=max_age, path="/", secure=True, httponly=True, samesite="lax")


def _current_session(request: Request, db: DbSession) -> AuthSession:
    cookie = request.cookies.get(SESSION_COOKIE)
    session = find_active_session(db, cookie, platform_settings()) if cookie else None
    if session is None:
        raise AuthenticationError("no live session")
    return session


@router.get("/login", status_code=status.HTTP_302_FOUND)
def login(
    provider: Annotated[str, Query(description="The identity provider: internal")] = "internal",
    return_to: Annotated[str, Query(description="A path on this application to return to")] = "/",
) -> RedirectResponse:
    """Start the authorisation code flow with PKCE."""
    configured = get_providers().named(provider)
    if configured is None or not is_safe_return_path(return_to):
        return RedirectResponse(
            origin_of(str(platform_settings().app_public_url)) + "/", status_code=status.HTTP_302_FOUND
        )
    authorization_url, flow = start_sign_in(configured, _redirect_uri(), return_to)
    response = RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)
    _set_cookie(response, FLOW_COOKIE, flow.to_cookie(), FLOW_COOKIE_MAX_AGE_SECONDS)
    return response


def _read_flow(cookie: str | None) -> SignInFlow | None:
    if not cookie:
        return None
    try:
        return SignInFlow.from_cookie(cookie)
    except AuthenticationError:
        return None


def _restart(flow: SignInFlow | None) -> RedirectResponse | None:
    """Start the sign-in again for the same page, unless this flow was already a restart."""
    if flow is not None and flow.restarted:
        return None
    provider = get_providers().named(flow.provider if flow is not None else "internal")
    if provider is None:
        return None
    authorization_url, restarted = start_sign_in(
        provider, _redirect_uri(), flow.return_to if flow is not None else "/", restarted=True
    )
    response = RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)
    _set_cookie(response, FLOW_COOKIE, restarted.to_cookie(), FLOW_COOKIE_MAX_AGE_SECONDS)
    return response


def _failure_page(request: Request, flow: SignInFlow | None) -> HTMLResponse:
    """A plain page for a person whose sign-in failed, with a way to try again."""
    query = urlencode({"provider": "internal", "return_to": flow.return_to if flow is not None else "/"})
    correlation_id = html.escape(str(getattr(request.state, "correlation_id", "")))
    response = HTMLResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Sign-in failed</title></head>
<body style="font-family: sans-serif; max-width: 36rem; margin: 3rem auto; padding: 0 1rem">
<h1>Sign-in failed</h1>
<p>The sign-in could not be completed.</p>
<p><a href="/api/auth/login?{html.escape(query)}">Try again</a></p>
<p>If it keeps failing, contact support with this correlation ID: <code>{correlation_id}</code></p>
</body></html>""",
    )
    response.delete_cookie(FLOW_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    return response


@router.get("/callback", status_code=status.HTTP_302_FOUND, response_model=None)
def callback(
    request: Request,
    db: DbSession,
    http: HttpClient,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse | HTMLResponse:
    """Exchange the code, validate the ID token, create the session and return to the application.

    A sign-in whose flow is missing, expired or superseded (a reply after too long, from an old tab, or
    replayed by the back button) is started again once for the same page. Any other failure, or a
    second stale sign-in in a row, shows a page saying sign-in failed (specs/50-auth.md).
    """
    settings = platform_settings()
    flow = _read_flow(request.cookies.get(FLOW_COOKIE))
    provider = get_providers().named(flow.provider) if flow is not None else None

    if error is not None or not code or not state:
        logger.info("Sign-in returned without a code", extra={"provider_error": error})
        return _failure_page(request, flow)
    if flow is None or provider is None or flow.is_expired() or state != flow.state:
        logger.info("Sign-in flow missing, expired or superseded")
        return _restart(flow) or _failure_page(request, flow)
    try:
        caller = finish_sign_in(provider, flow, code, _redirect_uri(), settings, http)
    except AuthenticationError:
        return _failure_page(request, flow)
    cookie_value, _ = create_session(db, caller, settings)

    response = RedirectResponse(
        origin_of(str(settings.app_public_url)) + flow.return_to, status_code=status.HTTP_302_FOUND
    )
    _set_cookie(response, SESSION_COOKIE, cookie_value, settings.session_max_hours * 3600)
    response.delete_cookie(FLOW_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    return response


@router.get("/session", response_model=SessionResponse)
def session(request: Request, db: DbSession) -> SessionResponse:
    """Who is signed in, their roles and the session's cross-site request forgery token; 401 otherwise."""
    current = _current_session(request, db)
    return SessionResponse(
        display_name=current.display_name,
        actor_type=current.actor_type,
        roles=sorted(current.roles),
        csrf_token=current.csrf_token,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, db: DbSession) -> JSONResponse:
    """End the session, clear the cookie and return the provider's sign-out address."""
    settings = platform_settings()
    current = _current_session(request, db)
    check_csrf(request, current, str(settings.app_public_url))
    provider = get_providers().named(current.provider)
    delete_session(db, current)
    logout_url = sign_out_address(provider, str(settings.app_public_url)) if provider else None
    response = JSONResponse(LogoutResponse(logout_url=logout_url).model_dump())
    response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="lax")
    return response
