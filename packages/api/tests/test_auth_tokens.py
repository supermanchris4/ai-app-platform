"""Unit tests for bearer token validation (specs/20-api-scaffold.md#authentication-and-authorisation)."""

import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from ai_app_platform.auth.context import ActorType, AuthenticationError
from ai_app_platform.auth.providers import Providers
from ai_app_platform.auth.tokens import CLOCK_SKEW_SECONDS, validate_bearer_token
from ai_app_platform.settings import PlatformSettings
from ai_app_platform.testing import TEST_ISSUER, TestIssuer


@pytest.fixture
def issuer() -> TestIssuer:
    return TestIssuer()


SETTINGS = PlatformSettings(
    app_environment="local",
    app_public_url="http://localhost:5173",  # pyright: ignore[reportArgumentType]  # validated from a string
    auth_internal_metadata_url="http://localhost:9000/internal/.well-known/openid-configuration",  # pyright: ignore[reportArgumentType]
    auth_internal_client_id="local-internal-app",
    database_host="localhost",
    database_name="example",
)


def validate(issuer: TestIssuer, token: str) -> Any:
    return validate_bearer_token(token, Providers(internal=issuer.provider()), SETTINGS)


def test_an_app_only_token_is_a_system_with_its_roles_and_client(issuer: TestIssuer) -> None:
    caller = validate(issuer, issuer(["system.write"], client_id="billing", subject="billing-app"))
    assert caller.actor_type == ActorType.SYSTEM
    assert caller.roles == frozenset({"system.write"})
    assert caller.subject == "billing-app"
    assert caller.client_id == "billing"


def test_a_delegated_token_is_a_person(issuer: TestIssuer) -> None:
    caller = validate(issuer, issuer(["editor.write"], delegated=True))
    assert caller.actor_type == ActorType.INTERNAL
    assert caller.display_name == "Test Person"


def test_v1_tokens_name_the_client_in_appid(issuer: TestIssuer) -> None:
    caller = validate(issuer, issuer(["system.read"], azp=None, appid="legacy-client"))
    assert caller.client_id == "legacy-client"


def test_the_subject_comes_from_the_configured_claim(issuer: TestIssuer) -> None:
    caller = validate(issuer, issuer(["system.read"], sub="pairwise-sub", oid="object-id"))
    assert caller.subject == "object-id"


@pytest.mark.parametrize(
    ("description", "claims"),
    [
        ("expired", {"exp": -(CLOCK_SKEW_SECONDS + 5)}),
        ("not yet valid", {"nbf": CLOCK_SKEW_SECONDS + 30}),
        ("issued in the future", {"iat": CLOCK_SKEW_SECONDS + 30}),
        ("another issuer", {"iss": "https://elsewhere.test/internal"}),
        ("another audience", {"aud": "another-app"}),
        ("no expiry", {"exp": None}),
        ("no subject", {"oid": None}),
        ("roles not a list", {"roles": "system.read"}),
        ("app-only without roles", {"roles": []}),
    ],
)
def test_invalid_tokens_are_refused(issuer: TestIssuer, description: str, claims: dict[str, Any]) -> None:
    # Time claims are given as seconds from now, worked out when the test runs.
    now = int(time.time())
    timed = {
        name: now + value if name in ("exp", "nbf", "iat") and value is not None else value
        for name, value in claims.items()
    }
    merged = {**issuer.claims(["system.read"]), **timed}
    token = issuer.sign({key: value for key, value in merged.items() if value is not None})
    with pytest.raises(AuthenticationError):
        validate(issuer, token)


def test_a_small_clock_difference_is_allowed(issuer: TestIssuer) -> None:
    validate(issuer, issuer(["system.read"], iat=int(time.time()) + 5, nbf=int(time.time()) + 5))


def test_a_delegated_token_needs_the_user_scope(issuer: TestIssuer) -> None:
    with pytest.raises(AuthenticationError):
        validate(issuer, issuer(["editor.write"], delegated=True, scp="other_scope"))


def test_a_token_signed_by_another_key_is_refused(issuer: TestIssuer) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AuthenticationError):
        validate(issuer, issuer.sign(issuer.claims(["system.read"]), key=other_key))


def test_a_token_from_another_test_issuer_is_refused(issuer: TestIssuer) -> None:
    with pytest.raises(AuthenticationError):
        validate(issuer, TEST_ISSUER(["system.read"]))


@pytest.mark.parametrize("algorithm", ["HS256", "none"])
def test_only_rs256_is_accepted(issuer: TestIssuer, algorithm: str) -> None:
    token = jwt.encode(
        issuer.claims(["system.read"]),
        "a-shared-secret-of-at-least-32-bytes" if algorithm == "HS256" else None,
        algorithm=algorithm,
        headers={"kid": issuer.kid},
    )
    with pytest.raises(AuthenticationError):
        validate(issuer, token)


def test_a_token_without_a_key_id_is_refused(issuer: TestIssuer) -> None:
    token = jwt.encode(issuer.claims(["system.read"]), issuer.key, algorithm="RS256")
    with pytest.raises(AuthenticationError):
        validate(issuer, token)


def test_garbage_is_refused(issuer: TestIssuer) -> None:
    with pytest.raises(AuthenticationError):
        validate(issuer, "not-a-token")
