"""Server-side sign-in sessions and the session cookie (specs/50-auth.md#web-sign-in-the-api-as-backend-for-frontend).

The cookie holds only 32 random bytes; the `auth_sessions` table holds their SHA-256 hash. A session
ends SESSION_IDLE_MINUTES after its last use or SESSION_MAX_HOURS after sign-in, whichever is first.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    LargeBinary,
    String,
    UniqueConstraint,
    delete,
    func,
    or_,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from ai_app_platform.auth.context import ActorType, AuthContext
from ai_app_platform.database import Base
from ai_app_platform.settings import PlatformSettings

SESSION_COOKIE = "__Host-session"
# A session's last-used time is written at most this often, not on every request.
TOUCH_INTERVAL = timedelta(minutes=1)


class AuthSession(Base):
    """A web sign-in session (specs/30-data-model.md#213-auth_sessions)."""

    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    roles: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__: Any = (
        CheckConstraint("provider IN ('internal')", name="ck_auth_sessions_provider"),
        UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
        Index("ix_auth_sessions_expires_at", "expires_at"),
    )

    def context(self) -> AuthContext:
        return AuthContext(
            subject=self.subject,
            actor_type=ActorType(self.actor_type),
            provider=self.provider,
            roles=frozenset(self.roles),
            display_name=self.display_name,
        )


def hash_cookie(value: str) -> bytes:
    return hashlib.sha256(value.encode()).digest()


def create_session(
    db: Session, caller: AuthContext, settings: PlatformSettings, now: datetime | None = None
) -> tuple[str, AuthSession]:
    """Store a session for a person who has just signed in. Returns the cookie value and the row."""
    now = now or datetime.now(UTC)
    cookie_value = secrets.token_urlsafe(32)
    session = AuthSession(
        token_hash=hash_cookie(cookie_value),
        csrf_token=secrets.token_urlsafe(32),
        provider=caller.provider,
        subject=caller.subject,
        actor_type=caller.actor_type.value,
        display_name=caller.display_name,
        roles=sorted(caller.roles),
        created_at=now,
        updated_at=now,
        last_used_at=now,
        expires_at=now + timedelta(hours=settings.session_max_hours),
    )
    db.add(session)
    db.flush()
    return cookie_value, session


def find_active_session(
    db: Session, cookie_value: str, settings: PlatformSettings, now: datetime | None = None
) -> AuthSession | None:
    """The live session for a cookie, with its last-used time updated; None if absent or ended."""
    now = now or datetime.now(UTC)
    session = db.scalars(select(AuthSession).where(AuthSession.token_hash == hash_cookie(cookie_value))).first()
    if session is None:
        return None
    if session.expires_at <= now or session.last_used_at + timedelta(minutes=settings.session_idle_minutes) <= now:
        return None
    if now - session.last_used_at >= TOUCH_INTERVAL:
        session.last_used_at = now
        session.updated_at = now
    return session


def delete_session(db: Session, session: AuthSession) -> None:
    db.delete(session)
    db.flush()


def delete_ended_sessions(db: Session, settings: PlatformSettings, now: datetime | None = None) -> int:
    """Delete sessions past their maximum lifetime or idle limit. Returns how many."""
    now = now or datetime.now(UTC)
    result = db.execute(
        delete(AuthSession).where(
            or_(
                AuthSession.expires_at <= now,
                AuthSession.last_used_at <= now - timedelta(minutes=settings.session_idle_minutes),
            )
        )
    )
    return result.rowcount  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType, reportUnknownMemberType]
