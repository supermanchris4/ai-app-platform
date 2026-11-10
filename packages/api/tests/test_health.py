"""GET /api/health (specs/20-api-scaffold.md#health-endpoint)."""

from dataclasses import replace
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from ai_app_platform import config


def test_healthy_when_the_database_responds(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "version", "timestamp"}
    assert body["status"] == "healthy"
    assert body["version"] == "unknown"
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None
    assert response.headers["Cache-Control"] == "no-store"


def test_unhealthy_when_the_database_does_not_respond(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable() -> None:
        raise ConnectionError("database down")

    monkeypatch.setattr(config, "_configuration", replace(config.configuration(), session_factory=unavailable))
    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "checks": {"database": "unavailable"}}
    assert response.headers["Cache-Control"] == "no-store"


def test_needs_no_authentication(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200


def test_the_old_path_is_gone(client: TestClient) -> None:
    assert client.get("/health").status_code == 404
