"""Helpers for an application's migrations (specs/30-data-model.md#83-access-control).

Migrations run as the migration user, `{prefix}_migrator`, which owns the schema. Each migration that
creates a table calls `grant_runtime` for it, so the runtime user, `{prefix}_runtime`, can use it.

The platform's own tables are created by the application's migrations, not the platform's: a new
application's first migration calls `create_platform_tables`, then each later version's helper in
order (`add_platform_change_stamps`). An application already past its first migration calls a new
version's helper from a new migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from ai_app_platform.auth.context import ActorType

MIGRATOR_SUFFIX = "_migrator"
RUNTIME_SUFFIX = "_runtime"

# Tables the runtime user may only insert into and read.
APPEND_ONLY_TABLES = frozenset({"audit_records"})


def runtime_role(migrator: str) -> str:
    """Name the runtime user from the migration user: `{prefix}_migrator` gives `{prefix}_runtime`."""
    if not migrator.endswith(MIGRATOR_SUFFIX):
        raise RuntimeError(f"migrations run as the {MIGRATOR_SUFFIX[1:]} user, not {migrator!r}")
    return migrator.removesuffix(MIGRATOR_SUFFIX) + RUNTIME_SUFFIX


def runtime_grant_sql(table: str, role: str) -> str:
    """The GRANT statement giving `role` its privileges on `table`."""
    privileges = "SELECT, INSERT" if table in APPEND_ONLY_TABLES else "SELECT, INSERT, UPDATE, DELETE"
    return f'GRANT {privileges} ON TABLE "{table}" TO "{role}"'


def grant_runtime(*tables: str) -> None:
    """Grant the runtime user its privileges on `tables`. Call from a migration's upgrade()."""
    migrator = op.get_bind().execute(text("SELECT current_user")).scalar_one()
    role = runtime_role(migrator)
    for table in tables:
        op.execute(runtime_grant_sql(table, role))


def revoke_runtime(*tables: str) -> None:
    """Revoke the runtime user's privileges on `tables`. Call from a migration's downgrade()."""
    migrator = op.get_bind().execute(text("SELECT current_user")).scalar_one()
    role = runtime_role(migrator)
    for table in tables:
        # The table names come from the migration code and the role from the database, never from input.
        # nosemgrep: python.lang.security.audit.formatted-sql-query.formatted-sql-query, python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query  # noqa: E501
        op.execute(f'REVOKE ALL ON TABLE "{table}" FROM "{role}"')


def create_platform_tables(entity_types: Sequence[str] | None = None) -> None:
    """Create the platform's tables, `auth_sessions` and `audit_records`, with the runtime user's grants.

    Call from a new application's first migration's upgrade(). The schema is written out here, as a
    migration's is, and is the platform's version 1: a later change to it comes with its own helper.
    `entity_types`, if given, are the only entity types `audit_records` accepts.
    """
    op.create_table(
        "auth_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False),
        sa.Column("csrf_token", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("roles", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_auth_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
        sa.CheckConstraint("provider IN ('internal')", name="ck_auth_sessions_provider"),
    )
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])

    actor_types = ", ".join(f"'{actor_type.value}'" for actor_type in ActorType)
    audit_constraints = [sa.CheckConstraint(f"actor_type IN ({actor_types})", name="ck_audit_records_actor_type")]
    if entity_types:
        if not all(entity_type.replace("_", "").isalnum() for entity_type in entity_types):
            raise ValueError("entity types are letters, digits and underscores")
        names = ", ".join(f"'{entity_type}'" for entity_type in entity_types)
        audit_constraints.append(sa.CheckConstraint(f"entity_type IN ({names})", name="ck_audit_records_entity_type"))
    op.create_table(
        "audit_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_name", sa.String(255), nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("reason_code", sa.String(50), nullable=True),
        sa.Column("reason_text", sa.Text(), nullable=True),
        sa.Column("before_state", postgresql.JSONB(), nullable=True),
        sa.Column("after_state", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_records"),
        *audit_constraints,
    )
    op.create_index("ix_audit_records_entity", "audit_records", ["entity_type", "entity_id"])
    op.create_index("ix_audit_records_actor_id", "audit_records", ["actor_id"])
    op.create_index("ix_audit_records_action", "audit_records", ["action"])
    op.create_index("ix_audit_records_created_at", "audit_records", ["created_at"])
    op.create_index(
        "ix_audit_records_correlation_id",
        "audit_records",
        ["correlation_id"],
        postgresql_where=sa.text("correlation_id IS NOT NULL"),
    )
    grant_runtime("auth_sessions", "audit_records")


def add_platform_change_stamps() -> None:
    """Version 2 of the platform's tables: `audit_records` gains `updated_at`, as every table has one.

    The template's NFR-DAT-01: a record holds when it was created and when it was last changed, equal
    until its first change. An audit record never changes, so its `updated_at` is its `created_at`.
    Call from a migration's upgrade(), after `create_platform_tables`.
    """
    op.add_column(
        "audit_records",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("UPDATE audit_records SET updated_at = created_at")


def drop_platform_change_stamps() -> None:
    """Undo `add_platform_change_stamps`. Call from the same migration's downgrade()."""
    op.drop_column("audit_records", "updated_at")
