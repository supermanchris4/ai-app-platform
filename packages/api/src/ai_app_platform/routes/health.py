"""Health endpoint (specs/20-api-scaffold.md#health-endpoint). Platform module."""

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from ai_app_platform.config import configuration

router = APIRouter(tags=["Health"])


class HealthyResponse(BaseModel):
    status: Literal["healthy"] = "healthy"
    version: str = Field(..., description="The deployed version: the commit SHA, set by the pipeline")
    timestamp: datetime


class UnhealthyResponse(BaseModel):
    status: Literal["unhealthy"] = "unhealthy"
    checks: dict[str, str] = Field(..., description="Each failed check, such as database: unavailable")


NO_STORE = {"Cache-Control": "no-store"}


@router.get(
    "/api/health",
    response_model=HealthyResponse,
    responses={503: {"model": UnhealthyResponse, "description": "The database is unavailable"}},
)
def health_check() -> JSONResponse:
    """Check that the API can reach its database. Needs no authentication.

    Used by the container health check, the load balancer and the pipeline's check through CloudFront.
    """
    try:
        with configuration().session_factory() as session:
            session.execute(text("SELECT 1"))
    except Exception:
        unhealthy = UnhealthyResponse(checks={"database": "unavailable"})
        return JSONResponse(unhealthy.model_dump(), status_code=status.HTTP_503_SERVICE_UNAVAILABLE, headers=NO_STORE)

    healthy = HealthyResponse(version=configuration().settings().app_version, timestamp=datetime.now(UTC))
    return JSONResponse(healthy.model_dump(mode="json"), headers=NO_STORE)
