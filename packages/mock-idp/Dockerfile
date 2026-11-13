# The local mock identity provider (the template's 11-local-development.md). Never deployed.
# Published to GitHub Container Registry (README); each application mounts its roles and
# people file and sets MOCK_IDP_CONFIG to it (README).

FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv

FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72 AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72
# The release adds org.opencontainers.image.source, naming the repository it is built from.
LABEL org.opencontainers.image.description="Local mock OpenID Connect provider. Never deployed." \
      org.opencontainers.image.licenses="Apache-2.0"
# The provider needs no package installer at run time, and pip's own vendored packages are scanned
# like any other, so it is removed.
RUN python -m pip uninstall --yes --quiet pip \
    && groupadd --system app && useradd --system --gid app --home-dir /app app
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=app:app mock_idp.py ./
USER app
EXPOSE 9000
HEALTHCHECK --interval=5s --timeout=3s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:9000/health', timeout=2)"]
CMD ["uvicorn", "mock_idp:app", "--host", "0.0.0.0", "--port", "9000"]
