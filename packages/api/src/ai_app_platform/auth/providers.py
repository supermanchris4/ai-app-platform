"""OpenID Connect providers, read from their discovery documents at start-up.

Each provider's issuer, endpoints and signing keys are cached. Keys are fetched again when a token
names an unknown key ID, at most once a minute. The API refuses to start if a discovery document
cannot be read.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
from jwt import PyJWK, PyJWKSet

from ai_app_platform.settings import PlatformSettings

KEY_REFRESH_INTERVAL_SECONDS = 60


@dataclass(frozen=True)
class ProviderMetadata:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    end_session_endpoint: str | None = None

    @classmethod
    def from_discovery(cls, document: dict[str, Any]) -> "ProviderMetadata":
        return cls(
            issuer=document["issuer"],
            authorization_endpoint=document["authorization_endpoint"],
            token_endpoint=document["token_endpoint"],
            jwks_uri=document["jwks_uri"],
            end_session_endpoint=document.get("end_session_endpoint"),
        )


class UnknownSigningKeyError(Exception):
    """A token names a key the provider does not publish."""


class Provider:
    """One issuer the API trusts, with the application's client ID there."""

    def __init__(
        self,
        name: str,
        client_id: str,
        metadata: ProviderMetadata,
        fetch_keys: Callable[[], dict[str, Any]],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.name = name
        self.client_id = client_id
        self.metadata = metadata
        self._fetch_keys = fetch_keys
        self._clock = clock
        self._lock = threading.Lock()
        self._keys: dict[str, PyJWK] = {}
        self._fetched_at: float | None = None
        self._refresh_keys()

    def signing_key(self, kid: str) -> PyJWK:
        with self._lock:
            key = self._keys.get(kid)
            if key is None and self._may_refresh():
                self._refresh_keys()
                key = self._keys.get(kid)
        if key is None:
            raise UnknownSigningKeyError(kid)
        return key

    def _may_refresh(self) -> bool:
        return self._fetched_at is None or self._clock() - self._fetched_at >= KEY_REFRESH_INTERVAL_SECONDS

    def _refresh_keys(self) -> None:
        key_set = PyJWKSet.from_dict(self._fetch_keys())
        self._keys = {key.key_id: key for key in key_set.keys if key.key_id}
        self._fetched_at = self._clock()


def discover(name: str, metadata_url: str, client_id: str, http: httpx.Client) -> Provider:
    """Read a provider's discovery document and keys. Raises if either cannot be read."""
    response = http.get(metadata_url)
    response.raise_for_status()
    metadata = ProviderMetadata.from_discovery(response.json())

    def fetch_keys() -> dict[str, Any]:
        keys_response = http.get(metadata.jwks_uri)
        keys_response.raise_for_status()
        return keys_response.json()

    return Provider(name, client_id, metadata, fetch_keys)


@dataclass(frozen=True)
class Providers:
    internal: Provider
    external: Provider | None = None

    def named(self, name: str) -> Provider | None:
        return {"internal": self.internal, "external": self.external}.get(name)


_providers: Providers | None = None


def initialise_providers(settings: PlatformSettings) -> Providers:
    """Discover the configured providers once. Tests set their own with `set_providers` first."""
    global _providers  # noqa: PLW0603  # the one process-wide registry, set at start-up
    if _providers is None:
        http = httpx.Client(timeout=10)
        internal = discover(
            "internal", str(settings.auth_internal_metadata_url), settings.auth_internal_client_id, http
        )
        external = None
        if settings.auth_external_metadata_url and settings.auth_external_client_id:
            external = discover(
                "external", str(settings.auth_external_metadata_url), settings.auth_external_client_id, http
            )
        _providers = Providers(internal=internal, external=external)
    return _providers


def set_providers(providers: Providers | None) -> None:
    global _providers  # noqa: PLW0603
    _providers = providers


def get_providers() -> Providers:
    if _providers is None:
        raise RuntimeError("Providers are not initialised; the API discovers them at start-up")
    return _providers
