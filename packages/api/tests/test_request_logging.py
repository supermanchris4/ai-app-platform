"""Unit tests for the path template the request log records."""

import pytest
from fastapi import APIRouter, FastAPI, Request
from fastapi.testclient import TestClient

from ai_app_platform.middleware.request_logging import path_template


@pytest.fixture
def templates() -> list[str | None]:
    return []


@pytest.fixture
def client(templates: list[str | None]) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def record_template(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        templates.append(path_template(request))
        return response

    inner = APIRouter(prefix="/records")

    @inner.get("/{record_id}")
    def get_record(record_id: str) -> dict[str, str]:
        return {}

    @inner.get("/{record_id}/items/{item_id}")
    def get_item(record_id: str, item_id: int) -> dict[str, str]:
        return {}

    outer = APIRouter(prefix="/v1")
    outer.include_router(inner)
    app.include_router(outer, prefix="/api")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {}

    return TestClient(app)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/api/v1/records/abc", "/api/v1/records/{record_id}"),
        ("/api/v1/records/records/items/7", "/api/v1/records/{record_id}/items/{item_id}"),
        ("/health", "/health"),
        ("/api/v1/records", None),
    ],
)
def test_the_template_includes_every_router_prefix(
    client: TestClient, templates: list[str | None], path: str, expected: str | None
) -> None:
    client.get(path)
    assert templates == [expected]
