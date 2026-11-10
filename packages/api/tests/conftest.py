"""Fixtures for the tests that need a database.

They use the database named by TEST_DATABASE_URL, as its `{prefix}_migrator` user; the name must end
in `_test`, because its schema is dropped at the start of every run. The schema is then created by
`create_platform_tables`, the helper a new application's first migration calls, so every run tests
it. Without TEST_DATABASE_URL, the database tests are skipped locally and fail in CI.
"""

import os
from collections.abc import Callable, Generator

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session

from ai_app_platform.auth.context import ActorType, AuthContext
from ai_app_platform.auth.sessions import create_session
from ai_app_platform.dependencies import get_db
from ai_app_platform.migrations import create_platform_tables
from ai_app_platform.testing import TEST_ISSUER, TEST_SUBJECT

ENTITY_TYPES = ["record", "item"]


def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        if os.environ.get("CI"):
            pytest.fail("Set TEST_DATABASE_URL: the database tests must run in CI")
        pytest.skip("Set TEST_DATABASE_URL to run the database tests (README)")
    if not (make_url(url).database or "").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must name a database ending in _test; its schema is dropped")
    return url


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine]:
    """The test database, its schema dropped and rebuilt by `create_platform_tables` for this run."""
    engine = create_engine(database_url())
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        with Operations.context(MigrationContext.configure(connection)):
            create_platform_tables(entity_types=ENTITY_TYPES)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session]:
    """A session whose work is rolled back after the test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, autoflush=False, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_engine: Engine, db_session: Session) -> Generator[TestClient]:
    """A test client for the test application, whose requests use the test's session.

    Like get_db, each request commits when it succeeds and rolls back when it fails; here a commit
    only ends a savepoint, so the test's work is still rolled back afterwards.
    """
    from tests.application import app, session_factory

    session_factory.configure(bind=db_engine)

    def override_get_db() -> Generator[Session]:
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def bearer(roles: list[str], *, delegated: bool) -> dict[str, str]:
    return {"Authorization": f"Bearer {TEST_ISSUER(roles, delegated=delegated)}"}


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """An administrator calling with a delegated token."""
    return bearer(["admin.write"], delegated=True)


SignedIn = Callable[..., dict[str, str]]


@pytest.fixture
def signed_in(db_session: Session) -> SignedIn:
    """Creates a sign-in session; returns the headers a browser would send with it: the cookie, the
    cross-site request forgery token and the matching Origin."""
    from tests.application import APP_ORIGIN, SETTINGS

    def sign_in(roles: list[str], *, subject: str = TEST_SUBJECT, display_name: str = "Test Person") -> dict[str, str]:
        caller = AuthContext(
            subject=subject,
            actor_type=ActorType.INTERNAL,
            provider="internal",
            roles=frozenset(roles),
            display_name=display_name,
        )
        cookie_value, session = create_session(db_session, caller, SETTINGS)
        db_session.commit()  # setup is committed, as a real sign-in would be; still rolled back after the test
        return {
            "Cookie": f"__Host-session={cookie_value}",
            "X-CSRF-Token": session.csrf_token,
            "Origin": APP_ORIGIN,
        }

    return sign_in
