"""Unit tests for the platform settings and the deployed-environment checks (specs/20-api-scaffold.md#settings)."""

from typing import Any

import pytest
from pydantic import ValidationError

from ai_app_platform.settings import PlatformSettings

DEPLOYED: dict[str, Any] = {
    "app_environment": "prod",
    "app_public_url": "https://app.example",
    "auth_internal_metadata_url": "https://login.microsoftonline.com/tenant/v2.0/.well-known/openid-configuration",
    "auth_internal_client_id": "client-id",
    "auth_client_certificate_secret_arn": "arn:aws:secretsmanager:ap-southeast-2:000000000000:secret:cert",
    "database_host": "db.example",
    "database_name": "example",
    "database_ssl_mode": "verify-full",
    "database_credentials_secret_arn": "arn:aws:secretsmanager:ap-southeast-2:000000000000:secret:db",
    "database_user": None,
    "database_password": None,
}


def platform(**overrides: Any) -> PlatformSettings:
    return PlatformSettings(**{**DEPLOYED, **overrides})


def test_valid_deployed_settings_are_accepted() -> None:
    assert platform().app_environment == "prod"


@pytest.mark.parametrize("environment", ["dev", "test", "prod"])
def test_checks_apply_in_every_deployed_environment(environment: str) -> None:
    with pytest.raises(ValidationError, match="DATABASE_SSL_MODE"):
        platform(app_environment=environment, database_ssl_mode="disable")


def test_local_permits_what_deployed_environments_refuse() -> None:
    settings = platform(
        app_environment="local",
        app_public_url="http://localhost:5173",
        auth_internal_metadata_url="http://mock-idp:9000/internal/.well-known/openid-configuration",
        auth_client_certificate_secret_arn=None,
        database_ssl_mode="disable",
        database_credentials_secret_arn=None,
        database_user="example_runtime",
        database_password="local-only",
    )
    assert settings.app_environment == "local"


def test_metadata_url_must_use_https() -> None:
    with pytest.raises(ValidationError, match="AUTH_INTERNAL_METADATA_URL"):
        platform(
            auth_internal_metadata_url="http://login.microsoftonline.com/tenant/v2.0/.well-known/openid-configuration"
        )


def test_metadata_url_host_must_be_allowed() -> None:
    with pytest.raises(ValidationError, match="AUTH_INTERNAL_METADATA_URL"):
        platform(auth_internal_metadata_url="https://issuer.example/.well-known/openid-configuration")


def test_external_metadata_url_is_checked_against_wildcard_hosts() -> None:
    settings = platform(
        auth_external_metadata_url="https://tenant.ciamlogin.com/tenant/v2.0/.well-known/openid-configuration",
        auth_external_client_id="external-client-id",
    )
    assert settings.auth_external_metadata_url is not None
    with pytest.raises(ValidationError, match="AUTH_EXTERNAL_METADATA_URL"):
        platform(
            auth_external_metadata_url="https://ciamlogin.com.example/.well-known/openid-configuration",
            auth_external_client_id="external-client-id",
        )


def test_allowed_issuer_hosts_are_comma_separated() -> None:
    settings = platform(
        auth_allowed_issuer_hosts=" Issuer.Example , *.other.example",
        auth_internal_metadata_url="https://issuer.example/.well-known/openid-configuration",
    )
    assert settings.auth_allowed_issuer_hosts == ["issuer.example", "*.other.example"]


def test_public_url_must_use_https() -> None:
    with pytest.raises(ValidationError, match="APP_PUBLIC_URL"):
        platform(app_public_url="http://app.example")


def test_client_certificate_is_required() -> None:
    with pytest.raises(ValidationError, match="AUTH_CLIENT_CERTIFICATE_SECRET_ARN"):
        platform(auth_client_certificate_secret_arn=None)


def test_database_tls_verification_is_required() -> None:
    with pytest.raises(ValidationError, match="DATABASE_SSL_MODE"):
        platform(database_ssl_mode="disable")


def test_database_credentials_secret_is_required() -> None:
    with pytest.raises(ValidationError, match="DATABASE_CREDENTIALS_SECRET_ARN"):
        platform(database_credentials_secret_arn=None)


@pytest.mark.parametrize("field", ["database_user", "database_password"])
def test_local_database_credentials_are_refused(field: str) -> None:
    with pytest.raises(ValidationError, match="DATABASE_USER and DATABASE_PASSWORD"):
        platform(**{field: "local-only"})


def test_external_issuer_needs_a_client_id() -> None:
    with pytest.raises(ValidationError, match="AUTH_EXTERNAL_CLIENT_ID"):
        platform(auth_external_metadata_url="https://tenant.ciamlogin.com/.well-known/openid-configuration")


def test_unknown_time_zone_is_refused() -> None:
    with pytest.raises(ValidationError, match="unknown time zone"):
        platform(app_business_time_zone="Australia/Nowhere")


def test_password_is_never_shown() -> None:
    settings = platform(app_environment="local", database_password="local-only")
    assert "local-only" not in repr(settings)
