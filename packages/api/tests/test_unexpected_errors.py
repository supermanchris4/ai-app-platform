"""Unit tests for unexpected errors: logged with the request's IDs, and the request logged too."""

import json
import logging
from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_app_platform.errors import general_exception_handler
from ai_app_platform.logging_config import JsonFormatter
from ai_app_platform.middleware import CorrelationMiddleware, RequestLoggingMiddleware, UnexpectedErrorMiddleware

CORRELATION_ID = "5f0c7a4e-0000-4000-8000-000000000001"


class Lines(logging.Handler):
    """Keeps each log line as the JSON formatter writes it, while the request's context is in place."""

    def __init__(self) -> None:
        super().__init__()
        self.setFormatter(JsonFormatter())
        self.entries: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.entries.append(json.loads(self.format(record)))


@pytest.fixture
def lines() -> Generator[Lines]:
    handler = Lines()
    root = logging.getLogger()
    previous = root.level
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    yield handler
    root.removeHandler(handler)
    root.setLevel(previous)


@pytest.fixture
def client() -> TestClient:
    # The application's order: the unexpected error middleware is added first, so it runs innermost.
    stack = FastAPI()
    stack.add_exception_handler(Exception, general_exception_handler)
    stack.add_middleware(UnexpectedErrorMiddleware, handler=general_exception_handler)
    stack.add_middleware(RequestLoggingMiddleware)
    stack.add_middleware(CorrelationMiddleware)

    @stack.get("/broken")
    def broken() -> None:
        refused = " ".join(["row", "values", "the", "database", "refused"])
        raise RuntimeError(refused)

    return TestClient(stack, raise_server_exceptions=False)


def test_the_response_is_the_error_shape_with_the_id_headers(client: TestClient, lines: Lines) -> None:
    response = client.get("/broken", headers={"X-Correlation-ID": CORRELATION_ID})

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_ERROR"
    assert error["correlation_id"] == CORRELATION_ID
    assert response.headers["X-Correlation-ID"] == CORRELATION_ID
    assert response.headers["X-Request-ID"] == error["request_id"]


def test_the_error_is_logged_once_with_the_ids_and_without_its_message(client: TestClient, lines: Lines) -> None:
    response = client.get("/broken", headers={"X-Correlation-ID": CORRELATION_ID})

    errors = [entry for entry in lines.entries if entry["level"] == "ERROR"]
    assert len(errors) == 1
    assert errors[0]["message"] == "Unexpected error"
    assert errors[0]["correlation_id"] == CORRELATION_ID
    assert errors[0]["request_id"] == response.headers["X-Request-ID"]
    assert "row values the database refused" not in json.dumps(errors[0])


def test_the_request_is_logged_with_status_500(client: TestClient, lines: Lines) -> None:
    client.get("/broken", headers={"X-Correlation-ID": CORRELATION_ID})

    requests = [entry for entry in lines.entries if entry["message"] == "Request completed"]
    assert len(requests) == 1
    assert requests[0]["status_code"] == 500
    assert requests[0]["path_template"] == "/broken"
    assert requests[0]["correlation_id"] == CORRELATION_ID
