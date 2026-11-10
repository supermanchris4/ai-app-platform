"""A minimal application built on the platform, as an application would build one, for the tests
that need the platform's dependencies, routes and handlers working together (specs/20-api-scaffold.md)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from ai_app_platform.audit.service import AuditService
from ai_app_platform.auth.context import AuthContext
from ai_app_platform.auth.providers import Providers, set_providers
from ai_app_platform.auth.roles import require_role
from ai_app_platform.config import configure
from ai_app_platform.dependencies import DbSession, authenticate
from ai_app_platform.errors import general_exception_handler, install_error_handlers
from ai_app_platform.middleware import CorrelationMiddleware, RequestLoggingMiddleware, UnexpectedErrorMiddleware
from ai_app_platform.routes import auth, health
from ai_app_platform.settings import PlatformSettings
from ai_app_platform.testing import TEST_ISSUER

APP_ORIGIN = "http://localhost:5173"
SETTINGS = PlatformSettings(
    app_environment="local",
    app_public_url=APP_ORIGIN,  # pyright: ignore[reportArgumentType]  # validated from a string
    auth_internal_metadata_url="http://localhost:9000/internal/.well-known/openid-configuration",  # pyright: ignore[reportArgumentType]
    auth_internal_client_id="local-internal-app",
    database_host="localhost",
    database_name="example_test",
)

# The tests' issuer stands in for the internal provider, so nothing is discovered at start-up.
set_providers(Providers(internal=TEST_ISSUER.provider()))

# Health opens its own sessions from this factory; the tests bind it to the test database.
session_factory = sessionmaker[Session](autocommit=False, autoflush=False)
configure(settings=lambda: SETTINGS, session_factory=session_factory)

app = FastAPI()
install_error_handlers(app)
app.add_middleware(UnexpectedErrorMiddleware, handler=general_exception_handler)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationMiddleware)
app.include_router(health.router)
app.include_router(auth.router)

records = APIRouter(prefix="/api/v1/records")
Reader = Annotated[AuthContext, Depends(require_role(authenticate, "editor.write", "admin.write"))]
Writer = Annotated[AuthContext, Depends(require_role(authenticate, "admin.write"))]


class NewRecord(BaseModel):
    name: str


@records.get("")
def list_records(caller: Reader) -> list[str]:
    return []


@records.post("", status_code=status.HTTP_201_CREATED)
def create_record(record: NewRecord, caller: Writer, db: DbSession) -> dict[str, str]:
    entity_id = uuid.uuid4()
    AuditService().record(
        db,
        entity_type="record",
        entity_id=entity_id,
        action="created",
        actor_id=caller.subject,
        actor_type=caller.actor_type.value,
    )
    return {"id": str(entity_id)}


app.include_router(records)
