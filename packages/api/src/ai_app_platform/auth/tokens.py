"""Bearer access token validation (specs/20-api-scaffold.md#authentication-and-authorisation).

The API accepts only access tokens the internal issuer issued for the application's own
registration, validated for signature (RS256), issuer, audience, expiry and not-before on every
request. A token with `scp` is delegated: it must include AUTH_USER_SCOPE, and its actor is a person.
A token without `scp` is app-only: it must carry at least one role, and its actor is a system.
"""

import logging
from typing import Any

import jwt

from ai_app_platform.auth.context import ActorType, AuthContext, AuthenticationError
from ai_app_platform.auth.providers import Providers, UnknownSigningKeyError
from ai_app_platform.settings import PlatformSettings

logger = logging.getLogger(__name__)

# Allowed difference between the issuer's clock and the API's when checking iat, nbf and exp.
CLOCK_SKEW_SECONDS = 60


def validate_bearer_token(token: str, providers: Providers, settings: PlatformSettings) -> AuthContext:
    """The caller a bearer token proves. Raises AuthenticationError, logging the reason."""
    provider = providers.internal
    try:
        kid = jwt.get_unverified_header(token).get("kid")
        if not kid:
            raise AuthenticationError("token has no key ID")
        claims: dict[str, Any] = jwt.decode(
            token,
            provider.signing_key(kid),
            algorithms=["RS256"],
            audience=provider.client_id,
            issuer=provider.metadata.issuer,
            options={"require": ["exp", "iss", "aud"]},
            leeway=CLOCK_SKEW_SECONDS,
        )
    except (jwt.PyJWTError, UnknownSigningKeyError, AuthenticationError) as error:
        logger.info("Bearer token refused", extra={"reason": type(error).__name__})
        raise AuthenticationError("invalid token") from None

    subject = claims.get(settings.auth_subject_claim)
    roles = claims.get("roles", [])
    if not isinstance(subject, str) or not subject or not isinstance(roles, list):
        logger.info("Bearer token refused", extra={"reason": "missing subject or malformed roles"})
        raise AuthenticationError("invalid token")
    role_set = frozenset(role for role in roles if isinstance(role, str))  # pyright: ignore[reportUnknownVariableType]

    scopes = claims.get("scp")
    if scopes is not None:
        if not isinstance(scopes, str) or settings.auth_user_scope not in scopes.split():
            logger.info("Bearer token refused", extra={"reason": "delegated token without the user scope"})
            raise AuthenticationError("invalid token")
        actor_type = ActorType.INTERNAL
    else:
        if not role_set:
            logger.info("Bearer token refused", extra={"reason": "app-only token without roles"})
            raise AuthenticationError("invalid token")
        actor_type = ActorType.SYSTEM

    client_id = claims.get("azp") or claims.get("appid")
    return AuthContext(
        subject=subject,
        actor_type=actor_type,
        provider=provider.name,
        roles=role_set,
        display_name=claims.get("name") if isinstance(claims.get("name"), str) else None,
        client_id=client_id if isinstance(client_id, str) else None,
    )
