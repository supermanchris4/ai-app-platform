"""The audit record (specs/31-audit.md, specs/30-data-model.md). Platform module.

The table and its columns are the platform's. Check constraints on the entity and actor types are
the application's: it records its own entity types, and may hold actor types from before it used
the platform. A new application's first migration creates both with `create_platform_tables`.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ai_app_platform.database import Base


class AuditRecord(Base):
    """Immutable audit trail for all significant state changes."""

    __tablename__ = "audit_records"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # The name the actor signed in with, when they acted; None for callers with no name.
    actor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    audit_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # Equal to created_at, since the runtime user cannot change an audit record; held as every table holds it.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_audit_records_entity", "entity_type", "entity_id"),
        Index("ix_audit_records_actor_id", "actor_id"),
        Index("ix_audit_records_action", "action"),
        Index("ix_audit_records_created_at", "created_at"),
        Index(
            "ix_audit_records_correlation_id",
            "correlation_id",
            postgresql_where="correlation_id IS NOT NULL",
        ),
    )
