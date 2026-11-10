"""Sign-in, sessions, cross-site request forgery checks and actor types (specs/50-auth.md)."""

from collections.abc import Generator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import httpx
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_app_platform import config
from ai_app_platform.audit.models import AuditRecord
from ai_app_platform.auth.context import AccessDeniedError, AuthContext
from ai_app_platform.auth.sessions import AuthSession, hash_cookie
from ai_app_platform.auth.web_sign_in import FLOW_COOKIE, FLOW_LIFETIME_SECONDS, SignInFlow
from ai_app_platform.routes.auth import get_http_client
from ai_app_platform.settings import PlatformSettings
from ai_app_platform.testing import API_CLIENT_ID, ISSUER, TEST_ISSUER
from tests.application import app

APP = "http://localhost:5173"
PERSON = "00000000-0000-4000-8000-0000000000aa"


class TokenEndpoint:
    """Stands in for the issuer's token endpoint, recording what the API sends."""

    def __init__(self) -> None:
        self.requests: list[dict[str, list[str]]] = []
        self.id_token_claims: dict[str, Any] = {}
        self.status_code = 200

    def handle(self, request: httpx.Request) -> httpx.Response:
        form = parse_qs(request.content.decode())
        self.requests.append(form)
        if self.status_code != 200:
            return httpx.Response(self.status_code, json={"error": "invalid_grant"})
        return httpx.Response(200, json={"id_token": TEST_ISSUER.sign(self.id_token_claims)})


@pytest.fixture
def token_endpoint(client: TestClient) -> Generator[TokenEndpoint]:
    endpoint = TokenEndpoint()

    def http_client() -> Generator[httpx.Client]:
        with httpx.Client(transport=httpx.MockTransport(endpoint.handle)) as stub:
            yield stub

    app.dependency_overrides[get_http_client] = http_client
    yield endpoint
    app.dependency_overrides.pop(get_http_client, None)


def start(client: TestClient, return_to: str = "/records") -> tuple[SignInFlow, str]:
    response = client.get("/api/auth/login", params={"return_to": return_to}, follow_redirects=False)
    assert response.status_code == 302
    flow_cookie = response.cookies[FLOW_COOKIE]
    return SignInFlow.from_cookie(flow_cookie), response.headers["location"]


def id_token_claims(flow: SignInFlow, **overrides: Any) -> dict[str, Any]:
    claims = TEST_ISSUER.claims(["editor.write"], subject=PERSON, nonce=flow.nonce, name="Sam Editor")
    claims.pop("scp", None)
    claims.update(overrides)
    return claims


def finish(client: TestClient, flow: SignInFlow | None, *, state: str | None = None) -> httpx.Response:
    return client.get(
        "/api/auth/callback",
        params={"code": "the-code", "state": state or (flow.state if flow else "s")},
        headers={"Cookie": f"{FLOW_COOKIE}={flow.to_cookie()}"} if flow else {},
        follow_redirects=False,
    )


def restarted_flow(response: httpx.Response) -> SignInFlow:
    """The flow a callback started again, after checking it sends the browser to the provider."""
    assert response.status_code == 302
    assert response.headers["location"].startswith(f"{ISSUER}/authorize?")
    flow = SignInFlow.from_cookie(response.cookies[FLOW_COOKIE])
    assert parse_qs(urlparse(response.headers["location"]).query)["state"] == [flow.state]
    return flow


def assert_failure_page(response: httpx.Response, return_to: str) -> None:
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("text/html")
    assert "Sign-in failed" in response.text
    assert f'href="/api/auth/login?provider=internal&amp;return_to={quote(return_to, safe="")}"' in response.text
    assert response.headers["X-Correlation-ID"] in response.text
    assert f'{FLOW_COOKIE}=""' in response.headers["set-cookie"]


def session_cookie(response: httpx.Response) -> str:
    header = next(
        value
        for name, value in response.headers.multi_items()
        if name == "set-cookie" and value.startswith("__Host-session=")
    )
    return header.split(";")[0].split("=", 1)[1]


class TestSignIn:
    def test_login_redirects_to_the_provider_with_pkce(self, client: TestClient) -> None:
        flow, location = start(client)
        query = parse_qs(urlparse(location).query)
        assert location.startswith(f"{ISSUER}/authorize?")
        assert query["redirect_uri"] == [f"{APP}/api/auth/callback"]
        assert query["code_challenge_method"] == ["S256"]
        assert query["state"] == [flow.state]

    def test_the_flow_cookie_is_host_only_and_hidden_from_scripts(self, client: TestClient) -> None:
        response = client.get("/api/auth/login", follow_redirects=False)
        cookie = response.headers["set-cookie"].lower()
        for attribute in ("httponly", "secure", "samesite=lax", "path=/", "max-age=3600"):
            assert attribute in cookie
        assert "domain=" not in cookie

    @pytest.mark.parametrize("return_to", ["//evil.example", "https://evil.example/"])
    def test_login_refuses_to_return_elsewhere(self, client: TestClient, return_to: str) -> None:
        response = client.get("/api/auth/login", params={"return_to": return_to}, follow_redirects=False)
        assert response.headers["location"] == f"{APP}/"
        assert FLOW_COOKIE not in response.cookies

    def test_the_callback_creates_a_session_and_returns_to_the_page(
        self, client: TestClient, token_endpoint: TokenEndpoint, db_session: Session
    ) -> None:
        flow, _ = start(client)
        token_endpoint.id_token_claims = id_token_claims(flow)

        response = finish(client, flow)

        assert response.status_code == 302
        assert response.headers["location"] == f"{APP}/records"
        set_cookies = [value.lower() for name, value in response.headers.multi_items() if name == "set-cookie"]
        session_header = next(value for value in set_cookies if value.startswith("__host-session="))
        for attribute in ("httponly", "secure", "samesite=lax", "path=/"):
            assert attribute in session_header
        stored = db_session.scalars(
            select(AuthSession).where(AuthSession.token_hash == hash_cookie(session_cookie(response)))
        ).one()
        assert stored.subject == PERSON
        assert stored.roles == ["editor.write"]
        assert stored.display_name == "Sam Editor"

        exchange = token_endpoint.requests[0]
        assert exchange["code_verifier"] == [flow.code_verifier]
        assert exchange["client_id"] == [API_CLIENT_ID]

    def test_then_the_session_endpoint_describes_the_person(
        self, client: TestClient, token_endpoint: TokenEndpoint
    ) -> None:
        flow, _ = start(client)
        token_endpoint.id_token_claims = id_token_claims(flow)
        cookie = session_cookie(finish(client, flow))

        body = client.get("/api/auth/session", headers={"Cookie": f"__Host-session={cookie}"}).json()
        assert body["display_name"] == "Sam Editor"
        assert body["actor_type"] == "internal"
        assert body["roles"] == ["editor.write"]
        assert len(body["csrf_token"]) > 20

    @pytest.mark.parametrize(
        ("description", "overrides"),
        [
            ("wrong nonce", {"nonce": "another"}),
            ("wrong audience", {"aud": "another-app"}),
            ("expired", {"exp": 1}),
            ("no subject", {"oid": None}),
        ],
    )
    def test_an_invalid_id_token_is_refused(
        self, client: TestClient, token_endpoint: TokenEndpoint, description: str, overrides: dict[str, Any]
    ) -> None:
        flow, _ = start(client)
        token_endpoint.id_token_claims = {
            key: value for key, value in id_token_claims(flow, **overrides).items() if value is not None
        }
        assert_failure_page(finish(client, flow), "/records")

    def test_a_refused_exchange_shows_the_failure_page(self, client: TestClient, token_endpoint: TokenEndpoint) -> None:
        flow, _ = start(client)
        token_endpoint.status_code = 400
        assert_failure_page(finish(client, flow), "/records")


class TestStaleSignIn:
    """A sign-in that can be started again (specs/50-auth.md#web-sign-in-the-api-as-backend-for-frontend)."""

    def test_an_expired_flow_is_started_again_for_the_same_page(
        self, client: TestClient, token_endpoint: TokenEndpoint
    ) -> None:
        flow, _ = start(client, "/records?name=example")
        expired = replace(flow, started_at=flow.started_at - FLOW_LIFETIME_SECONDS - 1)

        again = restarted_flow(finish(client, expired))

        assert token_endpoint.requests == []
        assert again.return_to == "/records?name=example"
        assert again.restarted
        assert again.state != flow.state

    def test_the_restarted_sign_in_completes(self, client: TestClient, token_endpoint: TokenEndpoint) -> None:
        flow, _ = start(client)
        again = restarted_flow(finish(client, replace(flow, started_at=0)))
        token_endpoint.id_token_claims = id_token_claims(again)

        response = finish(client, again)

        assert response.status_code == 302
        assert response.headers["location"] == f"{APP}/records"

    def test_a_state_from_another_attempt_is_started_again_before_any_exchange(
        self, client: TestClient, token_endpoint: TokenEndpoint
    ) -> None:
        flow, _ = start(client)
        assert restarted_flow(finish(client, flow, state="from-an-old-tab")).return_to == "/records"
        assert token_endpoint.requests == []

    def test_a_callback_without_the_flow_cookie_is_started_again_for_the_home_page(self, client: TestClient) -> None:
        assert restarted_flow(finish(client, None)).return_to == "/"

    def test_a_second_stale_sign_in_in_a_row_shows_the_failure_page(
        self, client: TestClient, token_endpoint: TokenEndpoint
    ) -> None:
        flow, _ = start(client, "/items")
        again = restarted_flow(finish(client, replace(flow, started_at=0)))

        assert_failure_page(finish(client, replace(again, started_at=0)), "/items")
        assert token_endpoint.requests == []

    @pytest.mark.parametrize("params", [{"error": "access_denied", "state": "s"}, {"state": "s"}, {"code": "c"}])
    def test_a_reply_without_a_code_shows_the_failure_page(
        self, client: TestClient, token_endpoint: TokenEndpoint, params: dict[str, str]
    ) -> None:
        flow, _ = start(client, "/items/new")
        response = client.get(
            "/api/auth/callback",
            params=params,
            headers={"Cookie": f"{FLOW_COOKIE}={flow.to_cookie()}"},
            follow_redirects=False,
        )
        assert_failure_page(response, "/items/new")
        assert token_endpoint.requests == []


class TestSessions:
    def test_the_session_endpoint_needs_a_session(self, client: TestClient) -> None:
        assert client.get("/api/auth/session").status_code == 401

    def test_a_bearer_token_is_not_a_session(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        assert client.get("/api/auth/session", headers=auth_headers).status_code == 401

    def test_a_session_reaches_the_api(self, client: TestClient, signed_in: Any) -> None:
        assert client.get("/api/v1/records", headers=signed_in(["editor.write"])).status_code == 200

    def test_an_unknown_cookie_is_401(self, client: TestClient) -> None:
        response = client.get("/api/v1/records", headers={"Cookie": "__Host-session=unknown"})
        assert response.status_code == 401

    @pytest.mark.parametrize(
        "changes",
        [
            {"expires_at": datetime.now(UTC) - timedelta(seconds=1)},
            {"last_used_at": datetime.now(UTC) - timedelta(minutes=31)},
        ],
    )
    def test_an_ended_session_is_401(
        self, client: TestClient, signed_in: Any, db_session: Session, changes: dict[str, datetime]
    ) -> None:
        headers = signed_in(["editor.write"])
        stored = db_session.scalars(select(AuthSession).order_by(AuthSession.created_at.desc())).first()
        assert stored is not None
        for name, value in changes.items():
            setattr(stored, name, value)
        db_session.flush()
        assert client.get("/api/v1/records", headers=headers).status_code == 401

    def test_logout_ends_the_session(self, client: TestClient, signed_in: Any) -> None:
        headers = signed_in(["editor.write"])

        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 200
        assert response.json()["logout_url"].startswith(f"{ISSUER}/logout?")
        assert "__Host-session=" in response.headers["set-cookie"]
        assert client.get("/api/auth/session", headers=headers).status_code == 401

    def test_logout_needs_the_csrf_token(self, client: TestClient, signed_in: Any) -> None:
        headers = signed_in(["editor.write"])
        response = client.post("/api/auth/logout", headers={**headers, "X-CSRF-Token": "wrong"})
        assert response.status_code == 403
        assert client.get("/api/auth/session", headers=headers).status_code == 200


class TestCrossSiteRequestForgery:
    """State-changing requests with the session cookie need the token and a matching Origin."""

    def test_with_both_the_request_passes_the_check(self, client: TestClient, signed_in: Any) -> None:
        response = client.post("/api/v1/records", headers=signed_in(["admin.write"]), json={})
        assert response.status_code not in (401, 403)

    @pytest.mark.parametrize(
        "change",
        [
            {"X-CSRF-Token": None},
            {"X-CSRF-Token": "wrong"},
            {"Origin": None},
            {"Origin": "https://evil.example"},
        ],
    )
    def test_without_either_it_is_403(self, client: TestClient, signed_in: Any, change: dict[str, Any]) -> None:
        headers = {**signed_in(["admin.write"]), **change}
        headers = {name: value for name, value in headers.items() if value is not None}
        response = client.post("/api/v1/records", headers=headers, json={})
        assert response.status_code == 403
        assert response.json()["error"]["message"] == "Not permitted"

    def test_reads_need_no_token(self, client: TestClient, signed_in: Any) -> None:
        headers = {"Cookie": signed_in(["editor.write"])["Cookie"]}
        assert client.get("/api/v1/records", headers=headers).status_code == 200

    def test_bearer_callers_need_no_token(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.post("/api/v1/records", headers=auth_headers, json={})
        assert response.status_code not in (401, 403)


class TestActorTypes:
    """The audit trail records the actor type the token or session proves."""

    def create_record(self, client: TestClient, headers: dict[str, str], name: str) -> str:
        response = client.post(
            "/api/v1/records",
            headers=headers,
            json={"name": name},
        )
        assert response.status_code == 201, response.text
        return response.json()["id"]

    def actor_of(self, db_session: Session, entity_id: str) -> tuple[str, str]:
        db_session.flush()
        record = db_session.scalars(select(AuditRecord).where(AuditRecord.entity_id == entity_id)).one()
        return record.actor_type, record.actor_id

    def test_a_delegated_token_is_recorded_as_internal(self, client: TestClient, db_session: Session) -> None:
        headers = {"Authorization": f"Bearer {TEST_ISSUER(['admin.write'], delegated=True, subject='person-a')}"}
        entity_id = self.create_record(client, headers, "actorTypeDelegated")
        assert self.actor_of(db_session, entity_id) == ("internal", "person-a")

    def test_a_session_is_recorded_as_internal(self, client: TestClient, signed_in: Any, db_session: Session) -> None:
        entity_id = self.create_record(client, signed_in(["admin.write"], subject="person-b"), "actorTypeSession")
        assert self.actor_of(db_session, entity_id) == ("internal", "person-b")


class TestAfterAuthentication:
    """The application's hook runs for each authenticated request and may refuse it (config.py)."""

    @pytest.fixture
    def hook(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        calls: list[str] = []

        def after_authentication(request: Request, caller: AuthContext, settings: PlatformSettings) -> None:
            calls.append(caller.subject)
            if caller.subject == "refused":
                raise AccessDeniedError("refused by the application")

        monkeypatch.setattr(
            config, "_configuration", replace(config.configuration(), after_authentication=after_authentication)
        )
        return calls

    def test_it_sees_each_caller(self, client: TestClient, hook: list[str]) -> None:
        headers = {"Authorization": f"Bearer {TEST_ISSUER(['editor.write'], delegated=True, subject='person-c')}"}
        assert client.get("/api/v1/records", headers=headers).status_code == 200
        assert hook == ["person-c"]

    def test_it_is_not_called_for_an_unauthenticated_request(self, client: TestClient, hook: list[str]) -> None:
        assert client.get("/api/v1/records").status_code == 401
        assert hook == []

    def test_it_can_refuse_the_request(self, client: TestClient, hook: list[str]) -> None:
        headers = {"Authorization": f"Bearer {TEST_ISSUER(['editor.write'], delegated=True, subject='refused')}"}
        assert client.get("/api/v1/records", headers=headers).status_code == 403
