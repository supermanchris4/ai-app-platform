"""Web sign-in: the authorisation code flow with PKCE, as a confidential client (specs/50-auth.md).

The flow's state, nonce, PKCE verifier and return path are held in the `__Host-sign-in` cookie
between `/api/auth/login` and `/api/auth/callback`. A flow is valid for FLOW_LIFETIME_SECONDS; the
cookie is kept for longer, so a callback that arrives too late can still be recognised and the
sign-in started again for the same page. In deployed environments the API
authenticates to the token endpoint with a `private_key_jwt` assertion signed by its client
certificate, read from Secrets Manager at start-up. Locally no certificate is configured and the
mock provider accepts the client ID alone.
"""

import base64
import hashlib
import json
import logging
import secrets
import time
import uuid
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import boto3
import httpx
import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from ai_app_platform.auth.context import ActorType, AuthContext, AuthenticationError
from ai_app_platform.auth.providers import Provider
from ai_app_platform.auth.tokens import CLOCK_SKEW_SECONDS
from ai_app_platform.settings import PlatformSettings

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

logger = logging.getLogger(__name__)

FLOW_COOKIE = "__Host-sign-in"
FLOW_LIFETIME_SECONDS = 600
FLOW_COOKIE_MAX_AGE_SECONDS = 3600
CALLBACK_PATH = "/api/auth/callback"
CLIENT_ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@dataclass(frozen=True)
class SignInFlow:
    """What the callback needs from the start of a sign-in."""

    provider: str
    state: str
    nonce: str
    code_verifier: str
    return_to: str
    started_at: int
    restarted: bool = False  # Started again by the callback after a stale sign-in

    def is_expired(self, now: float | None = None) -> bool:
        return (time.time() if now is None else now) - self.started_at > FLOW_LIFETIME_SECONDS

    def to_cookie(self) -> str:
        return _b64url(json.dumps(asdict(self)).encode())

    @classmethod
    def from_cookie(cls, value: str) -> "SignInFlow":
        try:
            data = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
            return cls(**data)
        except (ValueError, TypeError) as error:
            raise AuthenticationError("unreadable sign-in cookie") from error


def is_safe_return_path(path: str) -> bool:
    """A path on the application's own address: `/` followed by anything but another `/` or `\\`."""
    return (
        path.startswith("/")
        and not path.startswith("//")
        and "\\" not in path
        and not any(ord(character) < 0x20 for character in path)  # noqa: PLR2004  # control characters
    )


def start_sign_in(
    provider: Provider, redirect_uri: str, return_to: str, *, restarted: bool = False
) -> tuple[str, SignInFlow]:
    """The provider's authorisation address to send the browser to, and the flow to keep."""
    flow = SignInFlow(
        provider=provider.name,
        state=secrets.token_urlsafe(32),
        nonce=secrets.token_urlsafe(32),
        code_verifier=secrets.token_urlsafe(64),
        return_to=return_to,
        started_at=int(time.time()),
        restarted=restarted,
    )
    query = {
        "response_type": "code",
        "client_id": provider.client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile",
        "state": flow.state,
        "nonce": flow.nonce,
        "code_challenge": _b64url(hashlib.sha256(flow.code_verifier.encode()).digest()),
        "code_challenge_method": "S256",
    }
    return f"{provider.metadata.authorization_endpoint}?{urlencode(query)}", flow


@dataclass(frozen=True)
class ClientCertificate:
    """The application's client certificate and private key, for `private_key_jwt`."""

    certificate: x509.Certificate
    private_key: RSAPrivateKey

    @classmethod
    def from_pem(cls, certificate_pem: str, private_key_pem: str) -> "ClientCertificate":
        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
        if not isinstance(private_key, RSAPrivateKey):
            raise ValueError("the client certificate's key must be RSA")
        return cls(x509.load_pem_x509_certificate(certificate_pem.encode()), private_key)

    def client_assertion(self, client_id: str, token_endpoint: str, now: float | None = None) -> str:
        """A signed JWT authenticating the client to the token endpoint (RFC 7523).

        The header carries the certificate's thumbprints, by which Entra ID finds the uploaded key.
        """
        issued_at = int(time.time() if now is None else now)
        der = self.certificate.public_bytes(serialization.Encoding.DER)
        headers = {
            # The SHA-1 thumbprint is how Entra ID finds the key; it is an identifier, not a signature.
            # nosemgrep: python.cryptography.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1
            "x5t": _b64url(self.certificate.fingerprint(hashes.SHA1())),  # noqa: S303  # required by Entra ID
            "x5t#S256": _b64url(hashlib.sha256(der).digest()),
        }
        claims = {
            "iss": client_id,
            "sub": client_id,
            "aud": token_endpoint,
            "jti": str(uuid.uuid4()),
            "iat": issued_at,
            "nbf": issued_at,
            "exp": issued_at + 300,
        }
        return jwt.encode(claims, self.private_key, algorithm="RS256", headers=headers)


def load_client_certificate(secret_arn: str, client: "SecretsManagerClient | None" = None) -> ClientCertificate:
    """Read the certificate secret: JSON with `certificate` and `private_key`, both PEM."""
    if client is None:
        # Only the Secrets Manager stubs are installed, so boto3.client's other overloads are unknown.
        client = boto3.client("secretsmanager")  # pyright: ignore[reportUnknownMemberType]
    secret: dict[str, Any] = json.loads(client.get_secret_value(SecretId=secret_arn)["SecretString"])
    return ClientCertificate.from_pem(secret["certificate"], secret["private_key"])


_client_certificate: ClientCertificate | None = None


def initialise_web_sign_in(settings: PlatformSettings) -> None:
    """Read the client certificate at start-up where one is configured."""
    global _client_certificate  # noqa: PLW0603  # read once at start-up
    if settings.auth_client_certificate_secret_arn and _client_certificate is None:
        _client_certificate = load_client_certificate(settings.auth_client_certificate_secret_arn)


def set_client_certificate(certificate: ClientCertificate | None) -> None:
    global _client_certificate  # noqa: PLW0603
    _client_certificate = certificate


def client_authentication(provider: Provider) -> dict[str, str]:
    """The token request's client authentication fields."""
    if _client_certificate is None:
        return {"client_id": provider.client_id}
    return {
        "client_id": provider.client_id,
        "client_assertion_type": CLIENT_ASSERTION_TYPE,
        "client_assertion": _client_certificate.client_assertion(provider.client_id, provider.metadata.token_endpoint),
    }


def finish_sign_in(
    provider: Provider,
    flow: SignInFlow,
    code: str,
    redirect_uri: str,
    settings: PlatformSettings,
    http: httpx.Client,
) -> AuthContext:
    """Exchange the code and validate the ID token. Raises AuthenticationError, logging the reason."""
    response = http.post(
        provider.metadata.token_endpoint,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": flow.code_verifier,
            **client_authentication(provider),
        },
    )
    if not response.is_success:
        logger.info("Code exchange refused", extra={"status_code": response.status_code})
        raise AuthenticationError("code exchange refused")
    id_token = response.json().get("id_token")
    try:
        if not isinstance(id_token, str):
            raise AuthenticationError("no ID token")
        kid = jwt.get_unverified_header(id_token).get("kid") or ""
        claims: dict[str, Any] = jwt.decode(
            id_token,
            provider.signing_key(kid),
            algorithms=["RS256"],
            audience=provider.client_id,
            issuer=provider.metadata.issuer,
            options={"require": ["exp", "iss", "aud", "nonce"]},
            leeway=CLOCK_SKEW_SECONDS,
        )
    except Exception as error:
        logger.info("ID token refused", extra={"reason": type(error).__name__})
        raise AuthenticationError("invalid ID token") from None
    if not secrets.compare_digest(str(claims["nonce"]), flow.nonce):
        logger.info("ID token refused", extra={"reason": "nonce mismatch"})
        raise AuthenticationError("invalid ID token")

    subject = claims.get(settings.auth_subject_claim)
    roles = claims.get("roles", [])
    if not isinstance(subject, str) or not subject or not isinstance(roles, list):
        logger.info("ID token refused", extra={"reason": "missing subject or malformed roles"})
        raise AuthenticationError("invalid ID token")
    name = claims.get("name")
    return AuthContext(
        subject=subject,
        actor_type=ActorType.INTERNAL,
        provider=provider.name,
        roles=frozenset(role for role in roles if isinstance(role, str)),  # pyright: ignore[reportUnknownVariableType]
        display_name=name if isinstance(name, str) else None,
    )


def sign_out_address(provider: Provider, public_url: str) -> str | None:
    """The provider's sign-out address, returning to the application afterwards."""
    if provider.metadata.end_session_endpoint is None:
        return None
    query = urlencode({"post_logout_redirect_uri": public_url, "client_id": provider.client_id})
    return f"{provider.metadata.end_session_endpoint}?{query}"
