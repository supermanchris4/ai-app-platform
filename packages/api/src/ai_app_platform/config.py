"""What the application gives the platform once, at start-up: its settings, its database session
factory, and anything it adds to authentication. The platform's dependencies and routes read them
here, so the platform never imports the application."""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session

from ai_app_platform.auth.context import AuthContext
from ai_app_platform.settings import PlatformSettings

# Called with each authenticated request, its caller and the settings; an application uses it to
# add its own per-request work, such as rate limiting. It may raise to refuse the request.
AfterAuthentication = Callable[[Request, AuthContext, PlatformSettings], None]


@dataclass(frozen=True)
class Configuration:
    settings: Callable[[], PlatformSettings]
    session_factory: Callable[[], Session]
    after_authentication: AfterAuthentication | None = None


_configuration: Configuration | None = None


def configure(
    *,
    settings: Callable[[], PlatformSettings],
    session_factory: Callable[[], Session],
    after_authentication: AfterAuthentication | None = None,
) -> None:
    """Give the platform the application's settings and session factory. Call once, at start-up."""
    global _configuration  # noqa: PLW0603  # set once, by the application at start-up
    _configuration = Configuration(settings, session_factory, after_authentication)


def configuration() -> Configuration:
    """The application's configuration, which `configure` must have set."""
    if _configuration is None:
        raise RuntimeError("ai_app_platform.configure() has not been called")
    return _configuration


def platform_settings() -> PlatformSettings:
    """The application's settings, as the platform reads them."""
    return configuration().settings()
