"""Local mock OpenID Connect provider (the template's 11-local-development.md).

Stands in for the internal issuer on developers' machines, so the API signs people in and validates
tokens through the same code as in AWS. Never deployed. Each issuer generates a new RSA key pair at
start-up; no key is stored.

Each issuer, at /{issuer} (internal and external), serves:

- /.well-known/openid-configuration and /keys: discovery and signing keys
- /authorize: a page to choose a synthetic person and roles, completing the authorisation code flow
- /token: the authorisation code exchange, with PKCE; any client authentication is accepted
- /logout: the end of a sign-in
- /test-token: a signed access token for the subject, roles and token type in the request body

The discovery document gives the browser-facing address (MOCK_IDP_BROWSER_URL) for the pages a
browser opens and the container address (MOCK_IDP_ISSUER_URL) for the issuer and the endpoints the
API calls.
"""

import base64
import hashlib
import html
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal
from urllib.parse import urlencode, urlparse

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jwt.algorithms import RSAAlgorithm
from pydantic import BaseModel, Field

ISSUER_URL = os.environ.get("MOCK_IDP_ISSUER_URL", "http://mock-idp:9000").rstrip("/")
BROWSER_URL = os.environ.get("MOCK_IDP_BROWSER_URL", "http://localhost:9000").rstrip("/")
# The audience of test tokens when the request names none: the API's client ID.
DEFAULT_AUDIENCE = os.environ.get("MOCK_IDP_DEFAULT_AUDIENCE", "local-internal-app")
TOKEN_LIFETIME_SECONDS = 3600
CODE_LIFETIME_SECONDS = 120
DELEGATED_SCOPE = "access_as_user"

IssuerName = Literal["internal", "external"]


@dataclass(frozen=True)
class Person:
    """A synthetic person offered on the sign-in page. Never a real person."""

    oid: str
    name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class Configuration:
    """The application's roles and synthetic people, from the file the application supplies."""

    human_roles: tuple[str, ...]
    system_roles: tuple[str, ...]
    people: tuple[Person, ...]

    @property
    def roles(self) -> tuple[str, ...]:
        return self.human_roles + self.system_roles


class ConfigurationError(Exception):
    """The application's configuration file is missing or does not hold valid roles and people."""


def load_configuration(path: str | None) -> Configuration:
    """Read the application's roles and synthetic people (the template's 11-local-development.md).

    The provider holds no application's roles or people itself, so one image serves every
    application; it refuses to start without the file.
    """
    if not path:
        raise ConfigurationError("Set MOCK_IDP_CONFIG to the application's roles and people file")
    try:
        with open(path, encoding="utf-8") as file:
            raw = json.load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"No roles and people file at {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigurationError(f"{path} is not valid JSON: {error}") from error
    try:
        human_roles = tuple(str(role) for role in raw["human_roles"])
        system_roles = tuple(str(role) for role in raw["system_roles"])
        people = tuple(
            Person(str(person["oid"]), str(person["name"]), tuple(str(role) for role in person["roles"]))
            for person in raw["people"]
        )
    except (KeyError, TypeError) as error:
        raise ConfigurationError(f"{path} must hold human_roles, system_roles and people: {error}") from error
    if not people:
        raise ConfigurationError(f"{path} names no people")
    if len({person.oid for person in people}) != len(people):
        raise ConfigurationError(f"{path} names a person's oid twice")
    for person in people:
        unknown = set(person.roles) - set(human_roles)
        if unknown:
            raise ConfigurationError(f"{person.name}'s roles {sorted(unknown)} are not human roles in {path}")
    return Configuration(human_roles=human_roles, system_roles=system_roles, people=people)


CONFIGURATION = load_configuration(os.environ.get("MOCK_IDP_CONFIG"))


@dataclass
class PendingCode:
    client_id: str
    redirect_uri: str
    nonce: str | None
    code_challenge: str
    person: Person
    roles: tuple[str, ...]
    expires_at: float


@dataclass
class Issuer:
    name: str
    key: rsa.RSAPrivateKey = field(
        default_factory=lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048)
    )
    kid: str = field(default_factory=lambda: uuid.uuid4().hex)
    codes: dict[str, PendingCode] = field(default_factory=dict[str, PendingCode])

    @property
    def issuer(self) -> str:
        return f"{ISSUER_URL}/{self.name}"

    def sign(self, claims: dict[str, Any]) -> str:
        # The claims are made-up test identities, for local use only.
        # nosemgrep: python.jwt.security.audit.jwt-exposed-data.jwt-python-exposed-data
        return jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": self.kid})

    def jwk(self) -> dict[str, Any]:
        public_jwk: dict[str, Any] = RSAAlgorithm.to_jwk(self.key.public_key(), as_dict=True)
        return {**public_jwk, "kid": self.kid, "use": "sig", "alg": "RS256"}


ISSUERS: dict[str, Issuer] = {name: Issuer(name) for name in ("internal", "external")}

app = FastAPI(title="Mock identity provider", docs_url=None, redoc_url=None, openapi_url=None)


def issuer_named(name: str) -> Issuer:
    found = ISSUERS.get(name)
    if found is None:
        raise HTTPException(status_code=404, detail="Unknown issuer")
    return found


def token_claims(
    issuer: Issuer, *, subject: str, audience: str, roles: tuple[str, ...], client_id: str, name: str | None
) -> dict[str, Any]:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": issuer.issuer,
        "aud": audience,
        "sub": subject,
        "oid": subject,
        "azp": client_id,
        "iat": now,
        "nbf": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
        "ver": "2.0",
    }
    if roles:
        claims["roles"] = list(roles)
    if name:
        claims["name"] = name
    return claims


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/{issuer_name}/.well-known/openid-configuration")
def discovery(issuer_name: IssuerName) -> dict[str, Any]:
    issuer = issuer_named(issuer_name)
    return {
        "issuer": issuer.issuer,
        "authorization_endpoint": f"{BROWSER_URL}/{issuer_name}/authorize",
        "token_endpoint": f"{ISSUER_URL}/{issuer_name}/token",
        "jwks_uri": f"{ISSUER_URL}/{issuer_name}/keys",
        "end_session_endpoint": f"{BROWSER_URL}/{issuer_name}/logout",
        "response_types_supported": ["code"],
        "subject_types_supported": ["pairwise"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["private_key_jwt", "client_secret_post", "none"],
        "scopes_supported": ["openid", "profile"],
    }


@app.get("/{issuer_name}/keys")
def keys(issuer_name: IssuerName) -> dict[str, Any]:
    return {"keys": [issuer_named(issuer_name).jwk()]}


def check_redirect_uri(redirect_uri: str) -> None:
    parsed = urlparse(redirect_uri)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="redirect_uri must be an absolute http or https address")


@app.get("/{issuer_name}/authorize", response_class=HTMLResponse)
def authorize_page(
    issuer_name: IssuerName,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    response_type: Literal["code"] = "code",
    code_challenge_method: Literal["S256"] = "S256",
    nonce: str | None = None,
    scope: str = "openid",
) -> str:
    """The sign-in page: choose a synthetic person and the roles they hold for this sign-in."""
    issuer_named(issuer_name)
    check_redirect_uri(redirect_uri)
    hidden = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "nonce": nonce or "",
    }
    hidden_inputs = "".join(
        f'<input type="hidden" name="{name}" value="{html.escape(value)}">' for name, value in hidden.items()
    )
    people = "".join(
        f'<label><input type="radio" name="oid" value="{person.oid}"{" checked" if index == 0 else ""}> '
        f"{html.escape(person.name)} (default roles: {html.escape(', '.join(person.roles) or 'none')})</label><br>"
        for index, person in enumerate(CONFIGURATION.people)
    )
    roles = "".join(
        f'<label><input type="checkbox" name="roles" value="{html.escape(role)}"> {html.escape(role)}</label><br>'
        for role in CONFIGURATION.human_roles
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Mock sign-in ({html.escape(issuer_name)})</title></head>
<body style="font-family: sans-serif; max-width: 36rem; margin: 2rem auto">
<h1>Mock sign-in</h1>
<p>Local development only. Choose a synthetic person. Tick roles to replace their default roles.</p>
<form method="post" action="{BROWSER_URL}/{issuer_name}/authorize">
{hidden_inputs}
<fieldset><legend>Person</legend>{people}</fieldset>
<fieldset><legend>Roles for this sign-in</legend>{roles}</fieldset>
<p><button type="submit">Sign in</button></p>
</form></body></html>"""


@app.post("/{issuer_name}/authorize")
def authorize_complete(
    issuer_name: IssuerName,
    client_id: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    state: Annotated[str, Form()],
    code_challenge: Annotated[str, Form()],
    oid: Annotated[str, Form()],
    nonce: Annotated[str, Form()] = "",
    roles: Annotated[list[str] | None, Form()] = None,
) -> RedirectResponse:
    """Issue an authorisation code for the chosen person and send the browser back to the client."""
    issuer = issuer_named(issuer_name)
    check_redirect_uri(redirect_uri)
    person = next((candidate for candidate in CONFIGURATION.people if candidate.oid == oid), None)
    if person is None:
        raise HTTPException(status_code=400, detail="Unknown person")
    chosen_roles = tuple(role for role in (roles or []) if role in CONFIGURATION.human_roles) or person.roles
    code = secrets.token_urlsafe(32)
    issuer.codes[code] = PendingCode(
        client_id=client_id,
        redirect_uri=redirect_uri,
        nonce=nonce or None,
        code_challenge=code_challenge,
        person=person,
        roles=chosen_roles,
        expires_at=time.time() + CODE_LIFETIME_SECONDS,
    )
    separator = "&" if urlparse(redirect_uri).query else "?"
    return RedirectResponse(f"{redirect_uri}{separator}{urlencode({'code': code, 'state': state})}", status_code=303)


def s256(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


@app.post("/{issuer_name}/token")
def token(
    issuer_name: IssuerName,
    grant_type: Annotated[str, Form()],
    code: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    code_verifier: Annotated[str, Form()],
    client_id: Annotated[str | None, Form()] = None,
    client_assertion: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    """Exchange an authorisation code. Client authentication is accepted in any form."""
    issuer = issuer_named(issuer_name)
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    pending = issuer.codes.pop(code, None)
    if pending is None or pending.expires_at < time.time():
        raise HTTPException(status_code=400, detail="invalid_grant")
    if client_id is None and client_assertion is not None:
        # The stand-in accepts any client authentication by design; it only needs the client ID.
        # nosemgrep: python.jwt.security.unverified-jwt-decode.unverified-jwt-decode
        client_id = jwt.decode(client_assertion, options={"verify_signature": False}).get("iss")
    if client_id != pending.client_id or redirect_uri != pending.redirect_uri:
        raise HTTPException(status_code=400, detail="invalid_grant")
    if s256(code_verifier) != pending.code_challenge:
        raise HTTPException(status_code=400, detail="invalid_grant")

    person = pending.person
    id_claims = token_claims(
        issuer,
        subject=person.oid,
        audience=pending.client_id,
        roles=pending.roles,
        client_id=pending.client_id,
        name=person.name,
    )
    if pending.nonce:
        id_claims["nonce"] = pending.nonce
    access_claims = {**id_claims, "scp": DELEGATED_SCOPE}
    access_claims.pop("nonce", None)
    return {
        "token_type": "Bearer",
        "expires_in": TOKEN_LIFETIME_SECONDS,
        "id_token": issuer.sign(id_claims),
        "access_token": issuer.sign(access_claims),
    }


@app.get("/{issuer_name}/logout", response_class=HTMLResponse)
def logout(issuer_name: IssuerName, post_logout_redirect_uri: str | None = None) -> Any:
    issuer_named(issuer_name)
    if post_logout_redirect_uri:
        check_redirect_uri(post_logout_redirect_uri)
        return RedirectResponse(post_logout_redirect_uri, status_code=303)
    return "<!doctype html><title>Signed out</title><p>Signed out of the mock identity provider.</p>"


class TestTokenRequest(BaseModel):
    subject: str = Field(..., min_length=1, description="The sub and oid claims")
    roles: list[str] = Field(default_factory=list[str])
    delegated: bool = Field(False, description="A delegated token has the scp claim; an app-only token does not")
    client_id: str = Field("local-test-client", description="The calling client's ID, as the azp claim")
    audience: str = Field(DEFAULT_AUDIENCE, description="The API's client ID")
    name: str | None = None


@app.post("/{issuer_name}/test-token")
def test_token(issuer_name: IssuerName, request: TestTokenRequest) -> dict[str, Any]:
    """A signed access token for calling the API, as a source system or a signed-in person would."""
    issuer = issuer_named(issuer_name)
    unknown = sorted(set(request.roles) - set(CONFIGURATION.roles))
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown roles: {', '.join(unknown)}")
    claims = token_claims(
        issuer,
        subject=request.subject,
        audience=request.audience,
        roles=tuple(request.roles),
        client_id=request.client_id,
        name=request.name,
    )
    if request.delegated:
        claims["scp"] = DELEGATED_SCOPE
    return {"access_token": issuer.sign(claims), "token_type": "Bearer", "expires_in": TOKEN_LIFETIME_SECONDS}
