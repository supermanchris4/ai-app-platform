"""Tests for the platform's dependency declarations."""

from typing import get_args

from ai_app_platform.dependencies import DbSession


def test_db_session_commits_before_the_response_is_sent() -> None:
    """The database session dependency ends before the response, so its commit is not after it."""
    depends = get_args(DbSession)[1]
    assert depends.scope == "function"
