"""Unit tests for the JSON log formatter (specs/20-api-scaffold.md#logging)."""

import json
import logging
import sys
from typing import Any

from ai_app_platform.logging_config import JsonFormatter, correlation_id_var, request_id_var


def format_record(message: str = "Something happened", **extra: Any) -> dict[str, Any]:
    record = logging.LogRecord("tests", logging.INFO, __file__, 1, message, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    line = JsonFormatter().format(record)
    assert "\n" not in line
    return json.loads(line)


def test_a_line_is_one_json_object_with_the_standard_fields() -> None:
    entry = format_record()
    assert entry["level"] == "INFO"
    assert entry["logger"] == "tests"
    assert entry["message"] == "Something happened"
    assert entry["timestamp"].endswith("+00:00")


def test_messages_needing_escapes_stay_valid_json() -> None:
    assert format_record('He said "hi"\nthen left')["message"] == 'He said "hi"\nthen left'


def test_correlation_and_request_ids_come_from_the_context() -> None:
    correlation_token = correlation_id_var.set("correlation-1")
    request_token = request_id_var.set("request-1")
    try:
        entry = format_record()
    finally:
        correlation_id_var.reset(correlation_token)
        request_id_var.reset(request_token)
    assert entry["correlation_id"] == "correlation-1"
    assert entry["request_id"] == "request-1"


def test_ids_are_null_outside_a_request() -> None:
    entry = format_record()
    assert entry["correlation_id"] is None
    assert entry["request_id"] is None


def test_extra_fields_are_included() -> None:
    entry = format_record(job_id="job-1", rows=3)
    assert entry["job_id"] == "job-1"
    assert entry["rows"] == 3


def test_denied_extra_fields_are_dropped_whatever_their_case() -> None:
    entry = format_record(
        authorization="Bearer x", Cookie="c", token="t", password="p", email="e", oid="o", Subject="s", kept="yes"
    )
    assert entry["kept"] == "yes"
    for field in ("authorization", "Cookie", "token", "password", "email", "oid", "Subject"):
        assert field not in entry


def test_values_json_cannot_hold_are_written_as_text() -> None:
    assert format_record(when=object())["when"].startswith("<object object")


def test_exceptions_are_logged_by_type_and_frames_without_their_messages() -> None:
    # Built at run time, so the values appear in no source line the frames show.
    private_value = "-".join(["private", "attribute", "value"])
    cause = KeyError(private_value)
    error = RuntimeError(f"Failing row contains ({private_value})")
    try:
        try:
            raise cause
        except KeyError:
            raise error from cause
    except RuntimeError:
        record = logging.LogRecord("tests", logging.ERROR, __file__, 1, "Failed", None, None)
        record.exc_info = sys.exc_info()
    line = JsonFormatter().format(record)
    entry = json.loads(line)

    assert [link["type"] for link in entry["exception"]] == ["builtins.RuntimeError", "builtins.KeyError"]
    assert "raise error from cause" in entry["exception"][0]["traceback"]
    assert private_value not in line
