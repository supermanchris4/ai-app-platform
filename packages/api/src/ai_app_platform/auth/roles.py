"""Route authorisation by app role, with no hierarchy (specs/50-auth.md#app-roles)."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from ai_app_platform.auth.context import AccessDeniedError, AuthContext


def require_role(authenticate: Callable[..., AuthContext], *allowed_roles: str) -> Callable[[AuthContext], AuthContext]:
    """A dependency returning the caller when it holds at least one of `allowed_roles`."""

    def dependency(auth: Annotated[AuthContext, Depends(authenticate)]) -> AuthContext:
        if not auth.holds_any(allowed_roles):
            raise AccessDeniedError("missing role")
        return auth

    return dependency
