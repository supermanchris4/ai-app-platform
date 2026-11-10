"""Who is calling: the authentication context and actor types (specs/20-api-scaffold.md#actor-types)."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum


class ActorType(StrEnum):
    """What kind of actor acted, for audit records and logs."""

    INTERNAL = "internal"  # A person signed in through the internal provider
    SYSTEM = "system"  # Another system using an app-only token
    JOB = "job"  # A scheduled task of this application, with the job name as the subject


class AuthenticationError(Exception):
    """No valid token or session. Returned as 401; the reason is logged, never returned."""


class AccessDeniedError(Exception):
    """Authenticated, but a role or the cross-site request forgery check is missing. Returned as 403."""


@dataclass(frozen=True)
class AuthContext:
    """The authenticated caller."""

    subject: str
    actor_type: ActorType
    provider: str
    roles: frozenset[str]
    display_name: str | None = None
    # The calling client's ID for an app-only token (azp, or appid in v1 tokens); None for people.
    client_id: str | None = None

    def holds_any(self, roles: Iterable[str]) -> bool:
        return not self.roles.isdisjoint(roles)

    def highest_role(self, precedence: Sequence[str]) -> str | None:
        """The first role in `precedence` the caller holds, or None if it holds none of them."""
        return next((role for role in precedence if role in self.roles), None)
