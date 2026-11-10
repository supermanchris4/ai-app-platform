"""The declarative base, engine and credential provider (specs/20-api-scaffold.md#database-access).

Platform module. Nothing is built when it is imported: the application creates its engine with
`create_database_engine` from its settings. Locally the user and password come from settings.
In deployed environments they come from a Secrets Manager secret, fetched when a connection is
opened and reused for DATABASE_CREDENTIALS_CACHE_SECONDS, so a rotated password is picked up
without a redeployment.
"""

import json
import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NamedTuple

import boto3
import psycopg
from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import ConnectionPoolEntry

from ai_app_platform.settings import PlatformSettings

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

# The Amazon RDS certificate bundle, copied into the image by the Dockerfile.
RDS_CA_BUNDLE = "/opt/rds/global-bundle.pem"


class Base(DeclarativeBase):
    """Declarative base class for ORM models."""

    pass


class DatabaseCredentials(NamedTuple):
    username: str
    password: str


class SecretsManagerCredentials:
    """A database user's credentials from a Secrets Manager secret, reused for a while.

    The secret holds JSON with `username` and `password`, the format the Secrets Manager rotation
    functions for PostgreSQL use.
    """

    def __init__(
        self,
        secret_arn: str,
        cache_seconds: int,
        client: "SecretsManagerClient | None" = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._secret_arn = secret_arn
        self._cache_seconds = cache_seconds
        self._client = client
        self._clock = clock
        self._lock = threading.Lock()
        self._credentials: DatabaseCredentials | None = None
        self._fetched_at = 0.0

    def get(self) -> DatabaseCredentials:
        """The cached credentials, fetched again once they are older than the cache period."""
        with self._lock:
            if self._credentials is None or self._clock() - self._fetched_at >= self._cache_seconds:
                self._credentials = self._fetch()
                self._fetched_at = self._clock()
            return self._credentials

    def invalidate(self) -> None:
        """Forget the cached credentials, so the next `get` fetches them."""
        with self._lock:
            self._credentials = None

    def _fetch(self) -> DatabaseCredentials:
        if self._client is None:
            # Only the Secrets Manager stubs are installed, so boto3.client's other overloads are unknown.
            self._client = boto3.client("secretsmanager")  # pyright: ignore[reportUnknownMemberType]
        secret: dict[str, Any] = json.loads(self._client.get_secret_value(SecretId=self._secret_arn)["SecretString"])
        return DatabaseCredentials(username=secret["username"], password=secret["password"])


def is_authentication_failure(error: psycopg.OperationalError) -> bool:
    """Whether a connection failed because the server refused the credentials.

    psycopg gives no SQLSTATE for connection failures, so the server's message is checked.
    """
    return "authentication failed" in str(error)


def use_credentials(engine: Engine, credentials: SecretsManagerCredentials) -> None:
    """Open each of the engine's connections with credentials from `credentials`.

    If the server refuses them, they are fetched again once before the connection fails, in case
    the password was rotated since they were cached.
    """

    @event.listens_for(engine, "do_connect")
    def connect(  # pyright: ignore[reportUnusedFunction]  # registered by the decorator
        dialect: Dialect, connection_record: ConnectionPoolEntry, cargs: tuple[Any, ...], cparams: dict[str, Any]
    ) -> Any:
        current = credentials.get()
        try:
            return dialect.connect(*cargs, **{**cparams, "user": current.username, "password": current.password})
        except psycopg.OperationalError as error:
            if not is_authentication_failure(error):
                raise
        credentials.invalidate()
        current = credentials.get()
        return dialect.connect(*cargs, **{**cparams, "user": current.username, "password": current.password})


def database_url(settings: PlatformSettings) -> URL:
    """Build the connection URL from the database settings.

    The user and password are in the URL only locally; in deployed environments `use_credentials`
    supplies them for each connection.
    """
    query = {"sslmode": settings.database_ssl_mode}
    if settings.database_ssl_mode == "verify-full":
        query["sslrootcert"] = RDS_CA_BUNDLE
    return URL.create(
        "postgresql+psycopg",
        username=settings.database_user,
        password=settings.database_password.get_secret_value() if settings.database_password else None,
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
        query=query,
    )


def create_database_engine(settings: PlatformSettings, **engine_options: Any) -> Engine:
    """An engine for the configured database, with the credential provider where one is configured."""
    new_engine = create_engine(database_url(settings), pool_pre_ping=True, **engine_options)
    if settings.database_credentials_secret_arn:
        use_credentials(
            new_engine,
            SecretsManagerCredentials(
                settings.database_credentials_secret_arn, settings.database_credentials_cache_seconds
            ),
        )
    return new_engine
