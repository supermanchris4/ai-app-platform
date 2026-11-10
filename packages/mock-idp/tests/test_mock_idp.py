"""Tests for the local mock identity provider."""

import base64
import hashlib
import json
import re
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi.testclient import TestClient

import mock_idp

CLIENT_ID = "local-internal-app"
REDIRECT_URI = "http://localhost:5173/api/auth/callback"


@pytest.fixture
def client() -> TestClient:
    return TestClient(mock_idp.app)


def verify(client: TestClient, token: str, audience: str = CLIENT_ID, issuer: str = "internal") -> dict[str, Any]:
    key_set = jwt.PyJWKSet.from_dict(client.get(f"/{issuer}/keys").json())
    kid = jwt.get_unverified_header(token)["kid"]
    key = next(k for k in key_set.keys if k.key_id == kid)
    return jwt.decode(token, key.key, algorithms=["RS256"], audience=audience, issuer=mock_idp.ISSUERS[issuer].issuer)


def pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def sign_in(client: TestClient, challenge: str, *, roles: list[str] | None = None, person: int = 0) -> str:
    """Complete the sign-in page and return the authorisation code."""
    response = client.post(
        "/internal/authorize",
        data={
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "state": "state-1",
            "code_challenge": challenge,
            "nonce": "nonce-1",
            "oid": mock_idp.CONFIGURATION.people[person].oid,
            **({"roles": roles} if roles else {}),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = urlparse(response.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == REDIRECT_URI
    query = parse_qs(location.query)
    assert query["state"] == ["state-1"]
    return query["code"][0]


def exchange(client: TestClient, code: str, verifier: str, **overrides: str) -> Any:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
        "client_id": CLIENT_ID,
        **overrides,
    }
    return client.post("/internal/token", data=data)


def test_discovery_gives_browser_and_container_addresses(client: TestClient) -> None:
    document = client.get("/internal/.well-known/openid-configuration").json()
    assert document["issuer"] == f"{mock_idp.ISSUER_URL}/internal"
    assert document["authorization_endpoint"].startswith(mock_idp.BROWSER_URL)
    assert document["end_session_endpoint"].startswith(mock_idp.BROWSER_URL)
    assert document["token_endpoint"].startswith(mock_idp.ISSUER_URL)
    assert document["jwks_uri"].startswith(mock_idp.ISSUER_URL)


def test_each_issuer_has_its_own_keys(client: TestClient) -> None:
    internal = client.get("/internal/keys").json()["keys"][0]["kid"]
    external = client.get("/external/keys").json()["keys"][0]["kid"]
    assert internal != external


def test_unknown_issuers_are_refused(client: TestClient) -> None:
    assert client.get("/other/.well-known/openid-configuration").status_code == 422


def test_the_sign_in_page_escapes_what_it_echoes(client: TestClient) -> None:
    page = client.get(
        "/internal/authorize",
        params={"client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI, "state": '"><script>', "code_challenge": "c"},
    ).text
    assert "<script>" not in page
    assert "Eddie Editor" in page


def test_the_code_flow_issues_signed_id_and_access_tokens(client: TestClient) -> None:
    verifier, challenge = pkce()
    tokens = exchange(client, sign_in(client, challenge), verifier).json()

    id_token = verify(client, tokens["id_token"])
    assert id_token["oid"] == mock_idp.CONFIGURATION.people[0].oid
    assert id_token["name"] == "Eddie Editor"
    assert id_token["roles"] == ["editor.write"]
    assert id_token["nonce"] == "nonce-1"
    access_token = verify(client, tokens["access_token"])
    assert access_token["scp"] == "access_as_user"
    assert "nonce" not in access_token


def test_ticked_roles_replace_the_persons_defaults(client: TestClient) -> None:
    verifier, challenge = pkce()
    tokens = exchange(client, sign_in(client, challenge, roles=["admin.write", "editor.write"]), verifier).json()
    assert sorted(verify(client, tokens["id_token"])["roles"]) == ["admin.write", "editor.write"]


def test_a_person_without_roles_gets_no_roles_claim(client: TestClient) -> None:
    verifier, challenge = pkce()
    tokens = exchange(client, sign_in(client, challenge, person=2), verifier).json()
    assert "roles" not in verify(client, tokens["id_token"])


def test_a_wrong_code_verifier_is_refused(client: TestClient) -> None:
    _, challenge = pkce()
    response = exchange(client, sign_in(client, challenge), "wrong-verifier")
    assert response.status_code == 400


def test_a_code_is_used_once(client: TestClient) -> None:
    verifier, challenge = pkce()
    code = sign_in(client, challenge)
    assert exchange(client, code, verifier).status_code == 200
    assert exchange(client, code, verifier).status_code == 400


def test_the_redirect_uri_must_match(client: TestClient) -> None:
    verifier, challenge = pkce()
    response = exchange(client, sign_in(client, challenge), verifier, redirect_uri="http://localhost:5173/other")
    assert response.status_code == 400


def test_a_client_assertion_identifies_the_client(client: TestClient) -> None:
    verifier, challenge = pkce()
    assertion = jwt.encode({"iss": CLIENT_ID, "sub": CLIENT_ID}, "any-key-is-accepted", algorithm="HS256")
    data = {
        "grant_type": "authorization_code",
        "code": sign_in(client, challenge),
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
        "client_assertion": assertion,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    }
    assert client.post("/internal/token", data=data).status_code == 200


def test_app_only_test_tokens_carry_roles_and_no_scope(client: TestClient) -> None:
    response = client.post(
        "/internal/test-token", json={"subject": "billing-app", "roles": ["system.write"], "client_id": "billing"}
    )
    claims = verify(client, response.json()["access_token"])
    assert claims["roles"] == ["system.write"]
    assert claims["azp"] == "billing"
    assert claims["oid"] == "billing-app"
    assert "scp" not in claims


def test_delegated_test_tokens_carry_the_scope(client: TestClient) -> None:
    response = client.post(
        "/internal/test-token", json={"subject": "person-1", "roles": ["editor.write"], "delegated": True}
    )
    assert verify(client, response.json()["access_token"])["scp"] == "access_as_user"


def test_logout_returns_to_the_given_address(client: TestClient) -> None:
    response = client.get(
        "/internal/logout", params={"post_logout_redirect_uri": "http://localhost:5173/"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "http://localhost:5173/"


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "healthy"}


def test_no_real_person_is_offered() -> None:
    assert all(
        re.fullmatch(r"00000000-0000-4000-8000-0000000000\d\d", person.oid) for person in mock_idp.CONFIGURATION.people
    )


# --- The application's roles and people file --------------------------------------------------


def write(tmp_path: Path, content: object) -> str:
    path = tmp_path / "mock-idp.json"
    path.write_text(json.dumps(content))
    return str(path)


VALID = {
    "human_roles": ["reviewer.write"],
    "system_roles": ["feed.read"],
    "people": [{"oid": "00000000-0000-4000-8000-000000000009", "name": "Pat Example", "roles": ["reviewer.write"]}],
}


def test_the_provider_refuses_to_start_without_the_file(tmp_path: Path) -> None:
    with pytest.raises(mock_idp.ConfigurationError, match="Set MOCK_IDP_CONFIG"):
        mock_idp.load_configuration(None)
    with pytest.raises(mock_idp.ConfigurationError, match="No roles and people file"):
        mock_idp.load_configuration(str(tmp_path / "missing.json"))


def test_any_applications_roles_and_people_are_read(tmp_path: Path) -> None:
    configuration = mock_idp.load_configuration(write(tmp_path, VALID))

    assert configuration.human_roles == ("reviewer.write",)
    assert configuration.roles == ("reviewer.write", "feed.read")
    assert configuration.people[0].name == "Pat Example"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"people": []}, "names no people"),
        ({"human_roles": None}, "must hold human_roles"),
        (
            {"people": [{"oid": "00000000-0000-4000-8000-000000000009", "name": "Pat", "roles": ["feed.read"]}]},
            "are not human roles",
        ),
        ({"people": [VALID["people"][0], VALID["people"][0]]}, "oid twice"),
    ],
)
def test_a_file_that_does_not_make_sense_is_refused(tmp_path: Path, change: dict[str, Any], message: str) -> None:
    with pytest.raises(mock_idp.ConfigurationError, match=message):
        mock_idp.load_configuration(write(tmp_path, {**VALID, **change}))


def test_the_sign_in_page_offers_the_applications_human_roles(client: TestClient) -> None:
    page = client.get(
        "/internal/authorize",
        params={"client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI, "state": "s", "code_challenge": "c"},
    ).text

    offered = re.findall(r'name="roles" value="([^"]+)"', page)
    assert offered == ["editor.write", "admin.write"]


def test_a_test_token_with_an_unknown_role_is_refused(client: TestClient) -> None:
    response = client.post("/internal/test-token", json={"subject": "s", "roles": ["system.write", "root"]})

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown roles: root"
