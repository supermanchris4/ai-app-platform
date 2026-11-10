"""Unit tests for the runtime grants made by migrations."""

import pytest

from ai_app_platform.migrations import runtime_grant_sql, runtime_role


def test_runtime_role_is_named_from_the_migration_user() -> None:
    assert runtime_role("example_migrator") == "example_runtime"
    assert runtime_role("other_migrator") == "other_runtime"


def test_migrations_refuse_any_other_user() -> None:
    with pytest.raises(RuntimeError, match="migrator user"):
        runtime_role("example")


def test_audit_records_are_insert_and_read_only() -> None:
    assert (
        runtime_grant_sql("audit_records", "example_runtime")
        == 'GRANT SELECT, INSERT ON TABLE "audit_records" TO "example_runtime"'
    )


def test_other_tables_get_read_and_write() -> None:
    assert runtime_grant_sql("assertions", "example_runtime") == (
        'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "assertions" TO "example_runtime"'
    )
