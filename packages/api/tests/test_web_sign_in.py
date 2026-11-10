"""Unit tests for web sign-in helpers."""

import base64
import datetime
import json
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from ai_app_platform.auth.context import AuthenticationError
from ai_app_platform.auth.csrf import origin_of
from ai_app_platform.auth.web_sign_in import (
    FLOW_LIFETIME_SECONDS,
    ClientCertificate,
    SignInFlow,
    is_safe_return_path,
    load_client_certificate,
    sign_out_address,
    start_sign_in,
)
from ai_app_platform.testing import TestIssuer


@pytest.mark.parametrize("path", ["/", "/identities", "/identities/123?tab=links#top"])
def test_paths_on_the_application_are_safe(path: str) -> None:
    assert is_safe_return_path(path)


@pytest.mark.parametrize(
    "path", ["", "identities", "//evil.example", "/\\evil.example", "https://evil.example", "/a\nb"]
)
def test_other_addresses_are_not(path: str) -> None:
    assert not is_safe_return_path(path)


def test_the_flow_survives_its_cookie() -> None:
    flow = SignInFlow("internal", "state", "nonce", "verifier", "/identities", started_at=1000, restarted=True)
    assert SignInFlow.from_cookie(flow.to_cookie()) == flow


def test_a_flow_expires_after_its_lifetime() -> None:
    flow = SignInFlow("internal", "state", "nonce", "verifier", "/", started_at=1000)
    assert not flow.is_expired(now=1000 + FLOW_LIFETIME_SECONDS)
    assert flow.is_expired(now=1000 + FLOW_LIFETIME_SECONDS + 1)


def test_a_cookie_from_before_flows_had_a_start_time_is_refused() -> None:
    old = SignInFlow("internal", "state", "nonce", "verifier", "/", started_at=0).to_cookie()
    data = json.loads(base64.urlsafe_b64decode(old + "=" * (-len(old) % 4)))
    del data["started_at"]
    with pytest.raises(AuthenticationError):
        SignInFlow.from_cookie(base64.urlsafe_b64encode(json.dumps(data).encode()).decode())


def test_a_tampered_flow_cookie_is_refused() -> None:
    with pytest.raises(AuthenticationError):
        SignInFlow.from_cookie("not-base64-json")


def test_sign_in_starts_with_pkce_and_a_nonce() -> None:
    provider = TestIssuer().provider()
    url, flow = start_sign_in(provider, "http://localhost:5173/api/auth/callback", "/")
    query = parse_qs(urlparse(url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == [flow.state]
    assert query["nonce"] == [flow.nonce]
    assert query["client_id"] == [provider.client_id]
    assert flow.code_verifier not in url


def self_signed() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "platform-test")])
    now = datetime.datetime.now(datetime.UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    key_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    return certificate.public_bytes(serialization.Encoding.PEM).decode(), key_pem


def test_the_client_assertion_is_signed_by_the_certificate_and_names_it() -> None:
    certificate_pem, key_pem = self_signed()
    certificate = ClientCertificate.from_pem(certificate_pem, key_pem)
    assertion = certificate.client_assertion("app", "https://issuer.test/token")

    header = jwt.get_unverified_header(assertion)
    assert {"x5t", "x5t#S256"} <= set(header)
    claims = jwt.decode(
        assertion,
        certificate.certificate.public_key(),
        algorithms=["RS256"],  # type: ignore[arg-type]
        audience="https://issuer.test/token",
    )
    assert claims["iss"] == claims["sub"] == "app"
    assert claims["exp"] - claims["iat"] == 300


def test_the_certificate_is_read_from_its_secret() -> None:
    certificate_pem, key_pem = self_signed()

    class Stub:
        def get_secret_value(self, SecretId: str) -> dict[str, str]:  # noqa: N803  # boto3's parameter name
            return {"SecretString": json.dumps({"certificate": certificate_pem, "private_key": key_pem})}

    assert load_client_certificate("arn", Stub()).certificate.subject.rfc4514_string() == "CN=platform-test"  # type: ignore[arg-type]


def test_sign_out_returns_to_the_application() -> None:
    url = sign_out_address(TestIssuer().provider(), "http://localhost:5173/")
    assert url is not None
    assert parse_qs(urlparse(url).query)["post_logout_redirect_uri"] == ["http://localhost:5173/"]


@pytest.mark.parametrize(
    ("url", "origin"),
    [("http://localhost:5173/", "http://localhost:5173"), ("https://Spine.Example/app", "https://spine.example")],
)
def test_origin_of(url: str, origin: str) -> None:
    assert origin_of(url) == origin
