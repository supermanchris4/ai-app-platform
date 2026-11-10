# ai-app-platform: the API platform

The platform code every FastAPI application built from the AI application template needs, as one Python package, `ai_app_platform`. It implements the template's `20-api-scaffold.md`, `31-audit.md` and `50-auth.md`, and imports nothing of any application's.

| Module | What it provides |
|---|---|
| `config` | `configure(settings=..., session_factory=..., after_authentication=...)`: what the application gives the platform once, at start-up |
| `settings` | `PlatformSettings`, which the application's settings class extends, with the checks deployed environments need |
| `database` | The declarative `Base` the application's models use, `create_database_engine`, and the Secrets Manager credential provider |
| `dependencies` | `get_db`, `DbSession`, `authenticate` and `Auth` for FastAPI routes |
| `auth` | Sign-in and access: OIDC providers, web sign-in, server-side sessions, CSRF checks, bearer tokens, `require_role` |
| `audit` | The `audit_records` model and `AuditService` |
| `middleware` | Correlation and request IDs, request logging, unexpected errors |
| `errors` | The error response shape, `error_body`, and `install_error_handlers` |
| `routes` | `GET /api/health` (`routes.health`) and the `/api/auth/` sign-in endpoints (`routes.auth`) |
| `schemas` | The error and pagination schemas |
| `migrations` | `grant_runtime` and `revoke_runtime` for the runtime database user, and `create_platform_tables` for a new application's first migration |
| `logging_config` | One JSON log formatter |
| `testing` | `TestIssuer`, a key pair an application's tests sign tokens with |

## Installing it

Each release is a git tag, `api-v{version}`, on this public repository, so installing needs no credential. In the application's `pyproject.toml`:

```toml
[project]
dependencies = ["ai-app-platform"]

[tool.uv.sources]
ai-app-platform = { git = "https://github.com/supermanchris4/ai-app-platform", tag = "api-v0.1.0", subdirectory = "packages/api" }
```

`uv lock` records the tag's commit, so development, the pull request checks and the image all install the same code. uv fetches git sources with `git`, so an image's build stage needs it installed. Where that is unwelcome, install the wheel attached to the release instead, which `uv lock` records with its hash:

```toml
[tool.uv.sources]
ai-app-platform = { url = "https://github.com/supermanchris4/ai-app-platform/releases/download/api-v0.1.0/ai_app_platform-0.1.0-py3-none-any.whl" }
```

To upgrade, change the version in the tag (or the address), run `uv lock`, and read the [changelog](CHANGELOG.md).

## Using it

An application:

1. Declares its settings by extending `PlatformSettings`, and its models on `ai_app_platform.database.Base`.
2. Creates its engine with `create_database_engine(settings)` and a session factory from it.
3. Calls `ai_app_platform.config.configure(...)` with its settings, session factory and any `after_authentication` hook, adds the platform's middleware and `install_error_handlers(app)`, and includes `routes.health.router` and `routes.auth.router`.
4. In its first migration, calls `create_platform_tables(entity_types=[...])`.

## Developing

```bash
uv sync
uv run ruff check . && uv run ruff format --check . && uv run pyright
TEST_DATABASE_URL=postgresql+psycopg://{prefix}_migrator:{password}@localhost:5432/{prefix}_test uv run pytest
```

The tests need a PostgreSQL database whose name ends in `_test`, owned by a `{prefix}_migrator` user, with a `{prefix}_runtime` role; `tests/database-users.sql` creates them, as the pull request checks do.
