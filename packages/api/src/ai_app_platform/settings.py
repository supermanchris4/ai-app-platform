"""The platform's settings, validated at start-up (specs/20-api-scaffold.md#settings).

`PlatformSettings` holds the template's settings and the deployed-environment checks. An
application's settings class extends it with its own fields and checks, and the application
declares the one instance it reads (see `ai_app_platform.configure`).
"""

from fnmatch import fnmatchcase
from typing import Annotated, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import HttpUrl, PositiveInt, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode

AppEnvironment = Literal["local", "dev", "test", "prod"]


class PlatformSettings(BaseSettings):
    """The template's settings, common to every application built from it."""

    app_environment: AppEnvironment
    app_version: str = "unknown"
    app_public_url: HttpUrl
    api_base_path: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    app_business_time_zone: str = "Australia/Perth"

    auth_internal_metadata_url: HttpUrl
    auth_internal_client_id: str
    auth_external_metadata_url: HttpUrl | None = None
    auth_external_client_id: str | None = None
    auth_allowed_issuer_hosts: Annotated[list[str], NoDecode] = ["login.microsoftonline.com", "*.ciamlogin.com"]
    auth_subject_claim: str = "oid"
    auth_client_certificate_secret_arn: str | None = None
    auth_user_scope: str = "access_as_user"
    session_idle_minutes: PositiveInt = 30
    session_max_hours: PositiveInt = 10

    database_host: str
    database_port: PositiveInt = 5432
    database_name: str
    database_ssl_mode: Literal["verify-full", "disable"] = "verify-full"
    database_credentials_secret_arn: str | None = None
    database_user: str | None = None
    database_password: SecretStr | None = None
    database_credentials_cache_seconds: PositiveInt = 300

    @field_validator("auth_allowed_issuer_hosts", mode="before")
    @classmethod
    def _split_hosts(cls, value: object) -> object:
        if isinstance(value, str):
            return [host.strip().lower() for host in value.split(",") if host.strip()]
        return value

    @field_validator("app_business_time_zone")
    @classmethod
    def _known_time_zone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"unknown time zone {value!r}") from None
        return value

    @model_validator(mode="after")
    def _check_settings(self) -> Self:
        if (self.auth_external_metadata_url is None) != (self.auth_external_client_id is None):
            raise ValueError("AUTH_EXTERNAL_METADATA_URL and AUTH_EXTERNAL_CLIENT_ID are set together")
        if self.app_environment != "local":
            self._check_deployed()
        return self

    def _check_deployed(self) -> None:
        """Refuse settings that are permitted only on a developer's machine."""
        problems: list[str] = []
        metadata_urls = [("AUTH_INTERNAL_METADATA_URL", self.auth_internal_metadata_url)]
        if self.auth_external_metadata_url is not None:
            metadata_urls.append(("AUTH_EXTERNAL_METADATA_URL", self.auth_external_metadata_url))
        for name, url in metadata_urls:
            if url.scheme != "https" or not self._allowed_issuer_host(url.host or ""):
                problems.append(f"{name} must use HTTPS on a host in AUTH_ALLOWED_ISSUER_HOSTS")
        if self.app_public_url.scheme != "https":
            problems.append("APP_PUBLIC_URL must use HTTPS")
        if not self.auth_client_certificate_secret_arn:
            problems.append("AUTH_CLIENT_CERTIFICATE_SECRET_ARN is required")
        if self.database_ssl_mode != "verify-full":
            problems.append("DATABASE_SSL_MODE must be verify-full")
        if not self.database_credentials_secret_arn:
            problems.append("DATABASE_CREDENTIALS_SECRET_ARN is required")
        if self.database_user is not None or self.database_password is not None:
            problems.append("DATABASE_USER and DATABASE_PASSWORD are local only")
        if problems:
            raise ValueError(f"not permitted when APP_ENVIRONMENT is {self.app_environment}: " + "; ".join(problems))

    def _allowed_issuer_host(self, host: str) -> bool:
        return any(fnmatchcase(host.lower(), pattern) for pattern in self.auth_allowed_issuer_hosts)
