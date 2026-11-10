"""Test helpers for applications: a key pair the tests sign tokens with, registered as the internal provider."""

import time
import uuid
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from ai_app_platform.auth.providers import Provider, ProviderMetadata

TEST_SUBJECT = "test-subject"
TEST_CLIENT_ID = "test-client"
# Matches AUTH_INTERNAL_CLIENT_ID in tests/conftest.py, the audience the API expects.
API_CLIENT_ID = "local-internal-app"
ISSUER = "https://issuer.test/internal"


class TestIssuer:
    """Signs tokens with its own key, as the internal issuer would."""

    __test__ = False  # a helper, not a test class

    def __init__(self) -> None:
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = uuid.uuid4().hex
        self.metadata = ProviderMetadata(
            issuer=ISSUER,
            authorization_endpoint=f"{ISSUER}/authorize",
            token_endpoint=f"{ISSUER}/token",
            jwks_uri=f"{ISSUER}/keys",
            end_session_endpoint=f"{ISSUER}/logout",
        )

    def jwks(self) -> dict[str, Any]:
        public: dict[str, Any] = RSAAlgorithm.to_jwk(self.key.public_key(), as_dict=True)
        return {"keys": [{**public, "kid": self.kid, "use": "sig", "alg": "RS256"}]}

    def provider(self) -> Provider:
        return Provider("internal", API_CLIENT_ID, self.metadata, self.jwks)

    def sign(self, claims: dict[str, Any], *, key: Any = None, kid: str | None = None) -> str:
        # The claims are made-up test identities, for tests only.
        # nosemgrep: python.jwt.security.audit.jwt-exposed-data.jwt-python-exposed-data
        return jwt.encode(claims, key or self.key, algorithm="RS256", headers={"kid": kid or self.kid})

    def claims(
        self,
        roles: list[str],
        *,
        delegated: bool = False,
        subject: str = TEST_SUBJECT,
        client_id: str = TEST_CLIENT_ID,
        **overrides: Any,
    ) -> dict[str, Any]:
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": ISSUER,
            "aud": API_CLIENT_ID,
            "sub": subject,
            "oid": subject,
            "azp": client_id,
            "iat": now,
            "nbf": now,
            "exp": now + 3600,
            "roles": roles,
        }
        if delegated:
            claims["scp"] = "access_as_user"
            claims["name"] = "Test Person"
        claims.update(overrides)
        return {key: value for key, value in claims.items() if value is not None}

    def __call__(self, roles: list[str], *, delegated: bool = False, **overrides: Any) -> str:
        """A signed access token. Pass a claim as None to leave it out."""
        return self.sign(self.claims(roles, delegated=delegated, **overrides))


TEST_ISSUER = TestIssuer()
