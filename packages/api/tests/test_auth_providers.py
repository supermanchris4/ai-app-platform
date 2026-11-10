"""Unit tests for provider discovery and signing key refresh."""

from typing import Any

import httpx
import pytest

from ai_app_platform.auth.context import AccessDeniedError, ActorType, AuthContext
from ai_app_platform.auth.providers import KEY_REFRESH_INTERVAL_SECONDS, Provider, UnknownSigningKeyError, discover
from ai_app_platform.auth.roles import require_role
from ai_app_platform.testing import TestIssuer


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_discovery_reads_the_document_and_keys() -> None:
    issuer = TestIssuer()
    document = {
        "issuer": issuer.metadata.issuer,
        "authorization_endpoint": issuer.metadata.authorization_endpoint,
        "token_endpoint": issuer.metadata.token_endpoint,
        "jwks_uri": issuer.metadata.jwks_uri,
    }

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("openid-configuration"):
            return httpx.Response(200, json=document)
        return httpx.Response(200, json=issuer.jwks())

    provider = discover(
        "internal",
        "https://issuer.test/.well-known/openid-configuration",
        "app",
        httpx.Client(transport=httpx.MockTransport(respond)),
    )
    assert provider.metadata.issuer == issuer.metadata.issuer
    assert provider.metadata.end_session_endpoint is None
    assert provider.signing_key(issuer.kid).key_id == issuer.kid


def test_discovery_failure_stops_start_up() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    with pytest.raises(httpx.HTTPStatusError):
        discover("internal", "https://issuer.test/.well-known/openid-configuration", "app", client)


def test_an_unknown_key_refreshes_the_keys_at_most_once_a_minute() -> None:
    old, new = TestIssuer(), TestIssuer()
    served: list[dict[str, Any]] = [old.jwks()]
    fetches: list[int] = []

    def fetch() -> dict[str, Any]:
        fetches.append(1)
        return served[0]

    clock = Clock()
    provider = Provider("internal", "app", old.metadata, fetch, clock)
    served[0] = new.jwks()  # the provider rotates its key

    with pytest.raises(UnknownSigningKeyError):
        provider.signing_key(new.kid)  # too soon after start-up to fetch again
    clock.now += KEY_REFRESH_INTERVAL_SECONDS
    assert provider.signing_key(new.kid).key_id == new.kid
    assert len(fetches) == 2


def caller(*roles: str) -> AuthContext:
    return AuthContext(subject="s", actor_type=ActorType.INTERNAL, provider="internal", roles=frozenset(roles))


def test_the_highest_role_follows_the_precedence() -> None:
    precedence = ("admin.write", "editor.write", "system.write", "system.read")
    assert caller("system.read", "editor.write").highest_role(precedence) == "editor.write"
    assert caller("other").highest_role(precedence) is None


def test_require_role_accepts_any_listed_role_without_hierarchy() -> None:
    def authenticate() -> AuthContext:
        raise AssertionError("not called")

    check = require_role(authenticate, "editor.write", "admin.write")
    assert check(caller("editor.write")).roles == frozenset({"editor.write"})
    with pytest.raises(AccessDeniedError):
        check(caller("system.write"))
