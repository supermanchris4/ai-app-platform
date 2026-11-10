"""Unit tests for database access (specs/20-api-scaffold.md#database-access)."""

import json
from typing import Any

import psycopg
import pytest
from sqlalchemy import create_engine

from ai_app_platform.database import (
    RDS_CA_BUNDLE,
    DatabaseCredentials,
    SecretsManagerCredentials,
    database_url,
    use_credentials,
)
from ai_app_platform.settings import PlatformSettings

SECRET_ARN = "arn:aws:secretsmanager:ap-southeast-2:000000000000:secret:runtime"


class StubSecretsManager:
    """Stands in for the Secrets Manager client, returning each secret value in turn."""

    def __init__(self, *passwords: str) -> None:
        self.passwords = list(passwords)
        self.calls = 0

    def get_secret_value(self, SecretId: str) -> dict[str, str]:  # noqa: N803  # boto3's parameter name
        assert SecretId == SECRET_ARN
        password = self.passwords[min(self.calls, len(self.passwords) - 1)]
        self.calls += 1
        return {"SecretString": json.dumps({"username": "example_runtime", "password": password, "port": 5432})}


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def provider(client: StubSecretsManager, clock: Clock | None = None) -> SecretsManagerCredentials:
    return SecretsManagerCredentials(SECRET_ARN, cache_seconds=300, client=client, clock=clock or Clock())  # type: ignore[arg-type]


def test_credentials_are_read_from_the_secret() -> None:
    assert provider(StubSecretsManager("first")).get() == DatabaseCredentials("example_runtime", "first")


def test_credentials_are_reused_within_the_cache_period() -> None:
    client, clock = StubSecretsManager("first", "second"), Clock()
    credentials = provider(client, clock)
    credentials.get()
    clock.now += 299
    assert credentials.get().password == "first"
    assert client.calls == 1


def test_credentials_are_fetched_again_after_the_cache_period() -> None:
    client, clock = StubSecretsManager("first", "second"), Clock()
    credentials = provider(client, clock)
    credentials.get()
    clock.now += 300
    assert credentials.get().password == "second"
    assert client.calls == 2


def test_invalidated_credentials_are_fetched_again() -> None:
    client = StubSecretsManager("first", "second")
    credentials = provider(client)
    credentials.get()
    credentials.invalidate()
    assert credentials.get().password == "second"


class StubDialect:
    """Records each connection attempt; refuses passwords listed as rejected."""

    def __init__(self, rejected: set[str], error: str = 'password authentication failed for user "x"') -> None:
        self.rejected = rejected
        self.error = error
        self.attempts: list[dict[str, Any]] = []

    def connect(self, *cargs: Any, **cparams: Any) -> str:
        self.attempts.append(cparams)
        if cparams["password"] in self.rejected:
            raise psycopg.OperationalError(self.error)
        return "connection"


def connect_hook(dialect: StubDialect, credentials: SecretsManagerCredentials) -> Any:
    """Register the credential hook on an engine and return what it gives a new connection."""
    engine = create_engine("postgresql+psycopg://example-host/example")
    use_credentials(engine, credentials)
    cparams: dict[str, Any] = {"host": "example-host", "dbname": "example"}
    results = [
        hook(dialect, None, (), cparams)  # type: ignore[arg-type]
        for hook in engine.dialect.dispatch.do_connect  # type: ignore[attr-defined]
    ]
    return results[0]


def test_each_connection_uses_the_secrets_credentials() -> None:
    dialect = StubDialect(rejected=set())
    assert connect_hook(dialect, provider(StubSecretsManager("first"))) == "connection"
    assert dialect.attempts == [
        {"host": "example-host", "dbname": "example", "user": "example_runtime", "password": "first"}
    ]


def test_a_refused_password_is_fetched_again_once() -> None:
    client = StubSecretsManager("stale", "rotated")
    dialect = StubDialect(rejected={"stale"})
    credentials = provider(client)
    credentials.get()

    assert connect_hook(dialect, credentials) == "connection"
    assert [attempt["password"] for attempt in dialect.attempts] == ["stale", "rotated"]
    assert client.calls == 2


def test_a_second_refusal_fails_the_connection() -> None:
    dialect = StubDialect(rejected={"stale", "also-stale"})
    with pytest.raises(psycopg.OperationalError, match="authentication failed"):
        connect_hook(dialect, provider(StubSecretsManager("stale", "also-stale")))
    assert len(dialect.attempts) == 2


def test_other_connection_failures_are_not_retried() -> None:
    client = StubSecretsManager("first")
    dialect = StubDialect(rejected={"first"}, error="connection refused")
    with pytest.raises(psycopg.OperationalError, match="connection refused"):
        connect_hook(dialect, provider(client))
    assert len(dialect.attempts) == 1
    assert client.calls == 1


def settings(**overrides: Any) -> PlatformSettings:
    values: dict[str, Any] = {
        "app_environment": "local",
        "app_public_url": "http://localhost:5173",
        "auth_internal_metadata_url": "http://localhost:9000/internal/.well-known/openid-configuration",
        "auth_internal_client_id": "client",
        "database_host": "example-host",
        "database_name": "example",
    }
    return PlatformSettings(**{**values, **overrides})


def test_verified_tls_uses_the_rds_bundle() -> None:
    url = database_url(settings(database_ssl_mode="verify-full", database_user=None, database_password=None))
    assert url.query == {"sslmode": "verify-full", "sslrootcert": RDS_CA_BUNDLE}
    assert url.username is None


def test_local_connections_carry_the_local_credentials() -> None:
    url = database_url(settings(database_ssl_mode="disable", database_user="example_runtime", database_password="pw"))
    assert url.query == {"sslmode": "disable"}
    assert (url.username, url.password) == ("example_runtime", "pw")
