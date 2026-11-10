"""The database session and request authentication, as FastAPI dependencies.

Every request except /api/health and the /api/auth/ endpoints is authenticated here, in this order
(specs/20-api-scaffold.md#authentication-and-authorisation):

1. An `Authorization: Bearer` header, validated by auth/tokens.py.
2. Otherwise the `__Host-session` cookie, with the cross-site request forgery check for
   state-changing methods.
3. Otherwise 401.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ai_app_platform.audit.service import note_caller
from ai_app_platform.auth.context import AuthContext, AuthenticationError
from ai_app_platform.auth.csrf import check_csrf
from ai_app_platform.auth.providers import get_providers
from ai_app_platform.auth.sessions import SESSION_COOKIE, find_active_session
from ai_app_platform.auth.tokens import validate_bearer_token
from ai_app_platform.config import configuration


def get_db() -> Generator[Session]:
    """Yield a database session with automatic cleanup."""
    db = configuration().session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# scope="function" commits before the response is sent. With the default scope, FastAPI runs the
# code after `yield` once the response has gone, so a client could act on a write not yet committed.
DbSession = Annotated[Session, Depends(get_db, scope="function")]


def authenticate(request: Request, db: DbSession) -> AuthContext:
    """The caller, from a bearer token or the session cookie. Raises AuthenticationError (401)."""
    config = configuration()
    settings = config.settings()
    authorization = request.headers.get("Authorization")
    if authorization is not None:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthenticationError("malformed Authorization header")
        caller = validate_bearer_token(token.strip(), get_providers(), settings)
    else:
        cookie = request.cookies.get(SESSION_COOKIE)
        session = find_active_session(db, cookie, settings) if cookie else None
        if session is None:
            raise AuthenticationError("no bearer token or live session")
        check_csrf(request, session, str(settings.app_public_url))
        caller = session.context()

    # For the request log, which records what kind of actor called but never who.
    request.state.actor_type = caller.actor_type
    # For the audit records the request writes, which record who (specs/31-audit.md).
    note_caller(db, caller)
    if config.after_authentication is not None:
        config.after_authentication(request, caller, settings)
    return caller


Auth = Annotated[AuthContext, Depends(authenticate)]
