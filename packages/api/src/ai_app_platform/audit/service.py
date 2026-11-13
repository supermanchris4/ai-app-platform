"""Records audit events (specs/31-audit.md). Platform module: imports nothing of any application's."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ai_app_platform.audit.models import AuditRecord
from ai_app_platform.auth.context import AuthContext

# The key under which the authentication dependency notes the request's caller on its session.
CALLER_KEY = "caller"


def note_caller(session: Session, caller: AuthContext) -> None:
    """Note the request's caller on its session, so its audit records carry the caller's name."""
    session.info[CALLER_KEY] = caller


class AuditService:
    """Service for creating audit records."""

    def record(
        self,
        session: Session,
        *,
        entity_type: str,
        entity_id: UUID,
        action: str,
        actor_id: str,
        actor_type: str,
        correlation_id: str | None = None,
        reason_code: str | None = None,
        reason_text: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Record an auditable event.

        Args:
            session: Database session.
            entity_type: Type of entity being audited.
            entity_id: ID of the entity.
            action: The action being performed.
            actor_id: ID of the actor performing the action.
            actor_type: Type of actor (user, system, job).
            correlation_id: Optional correlation ID for request tracing.
            reason_code: Optional reason code for the action.
            reason_text: Optional reason text for the action.
            before_state: State before the change (changed fields only).
            after_state: State after the change (changed fields only).
            metadata: Optional additional metadata.

        Returns:
            The created audit record. When the actor is the request's caller, the record carries
            the name the caller signed in with.
        """
        caller = session.info.get(CALLER_KEY)
        actor_name = caller.display_name if isinstance(caller, AuthContext) and caller.subject == actor_id else None
        now = datetime.now(UTC)
        audit_record = AuditRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_name=actor_name,
            correlation_id=correlation_id,
            reason_code=reason_code,
            reason_text=reason_text,
            before_state=before_state,
            after_state=after_state,
            audit_metadata=metadata,
            created_at=now,
            updated_at=now,
        )
        session.add(audit_record)
        return audit_record
