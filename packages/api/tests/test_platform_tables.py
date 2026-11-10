"""The platform's tables, as `create_platform_tables` creates them for a new application, used by the
sessions and audit code (specs/30-data-model.md, specs/31-audit.md). Needs the test database."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_app_platform.audit.models import AuditRecord
from ai_app_platform.audit.service import AuditService, note_caller
from ai_app_platform.auth.context import ActorType, AuthContext
from ai_app_platform.auth.sessions import AuthSession, create_session, delete_ended_sessions, find_active_session
from ai_app_platform.database import Base
from ai_app_platform.settings import PlatformSettings

SETTINGS = PlatformSettings(
    app_environment="local",
    app_public_url="http://localhost:5173",  # pyright: ignore[reportArgumentType]  # validated from a string
    auth_internal_metadata_url="http://localhost:9000/internal/.well-known/openid-configuration",  # pyright: ignore[reportArgumentType]
    auth_internal_client_id="local-internal-app",
    database_host="localhost",
    database_name="example_test",
    session_idle_minutes=30,
    session_max_hours=10,
)
PERSON = AuthContext(
    subject="00000000-0000-4000-8000-000000000001",
    actor_type=ActorType.INTERNAL,
    provider="internal",
    roles=frozenset({"editor.write"}),
    display_name="Pat Example",
)


def test_the_helpers_tables_match_the_models(db_engine: Engine) -> None:
    assert {AuditRecord.__tablename__, AuthSession.__tablename__} <= set(Base.metadata.tables)
    with db_engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


def insert_audit(db: Session, *, actor_type: str = "internal", entity_type: str = "record") -> None:
    db.execute(
        text(
            "INSERT INTO audit_records (entity_type, entity_id, action, actor_id, actor_type) "
            "VALUES (:entity_type, :entity_id, 'created', 'someone', :actor_type)"
        ),
        {"entity_type": entity_type, "entity_id": uuid.uuid4(), "actor_type": actor_type},
    )


@pytest.mark.parametrize("actor_type", [actor_type.value for actor_type in ActorType])
def test_audit_records_accept_the_platforms_actor_types(db_session: Session, actor_type: str) -> None:
    insert_audit(db_session, actor_type=actor_type)


def test_audit_records_refuse_other_actor_types(db_session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_audit_records_actor_type"):
        insert_audit(db_session, actor_type="steward")


def test_audit_records_refuse_entity_types_the_application_did_not_name(db_session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_audit_records_entity_type"):
        insert_audit(db_session, entity_type="invoice")


def test_the_runtime_user_may_only_add_and_read_audit_records(db_engine: Engine) -> None:
    with db_engine.connect() as connection:
        runtime = connection.execute(text("SELECT replace(current_user, '_migrator', '_runtime')")).scalar_one()

        def may(table: str, privilege: str) -> bool:
            return bool(
                connection.execute(
                    text("SELECT has_table_privilege(:role, :table, :privilege)"),
                    {"role": runtime, "table": table, "privilege": privilege},
                ).scalar_one()
            )

        assert may("audit_records", "INSERT") and may("audit_records", "SELECT")
        assert not may("audit_records", "UPDATE") and not may("audit_records", "DELETE")
        assert all(may("auth_sessions", p) for p in ("SELECT", "INSERT", "UPDATE", "DELETE"))


def test_a_session_is_found_by_its_cookie_until_it_ends(db_session: Session) -> None:
    now = datetime.now(UTC)
    cookie, _ = create_session(db_session, PERSON, SETTINGS, now=now)

    found = find_active_session(db_session, cookie, SETTINGS, now=now + timedelta(minutes=5))
    assert found is not None and found.context().display_name == "Pat Example"
    assert find_active_session(db_session, "another-cookie", SETTINGS, now=now) is None
    assert find_active_session(db_session, cookie, SETTINGS, now=now + timedelta(hours=11)) is None


def test_ended_sessions_are_deleted(db_session: Session) -> None:
    now = datetime.now(UTC)
    create_session(db_session, PERSON, SETTINGS, now=now - timedelta(hours=1))
    create_session(db_session, PERSON, SETTINGS, now=now)

    assert delete_ended_sessions(db_session, SETTINGS, now=now) == 1


def test_an_audit_record_carries_the_callers_name_when_the_caller_acted(db_session: Session) -> None:
    note_caller(db_session, PERSON)
    service = AuditService()

    own = service.record(
        db_session,
        entity_type="record",
        entity_id=uuid.uuid4(),
        action="created",
        actor_id=PERSON.subject,
        actor_type=PERSON.actor_type.value,
    )
    other = service.record(
        db_session,
        entity_type="record",
        entity_id=uuid.uuid4(),
        action="deleted",
        actor_id="nightly-job",
        actor_type=ActorType.JOB.value,
    )
    db_session.flush()

    assert own.actor_name == "Pat Example"
    assert other.actor_name is None
