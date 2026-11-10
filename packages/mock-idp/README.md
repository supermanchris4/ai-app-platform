# ai-app-platform: the mock identity provider

A local OpenID Connect provider that stands in for the internal issuer on developers' machines, so an application's API signs people in and validates tokens through the same code as in AWS. It implements the mock identity provider in the template's `11-local-development.md`. **Never deployed.** Each issuer generates a new key pair at start-up; no key is stored.

Each issuer, at `/internal` and `/external`, serves discovery and signing keys, a sign-in page to choose a synthetic person and their roles, the authorisation code exchange with PKCE, sign-out, and `/test-token`, which signs an access token for the subject, roles and token type in the request body.

## The application's roles and people

The provider holds no application's roles or people. Each application supplies a file, and the provider refuses to start without it:

```json
{
  "human_roles": ["editor.write", "admin.write"],
  "system_roles": ["system.read", "system.write"],
  "people": [
    { "oid": "00000000-0000-4000-8000-000000000001", "name": "Eddie Editor", "roles": ["editor.write"] }
  ]
}
```

People are synthetic, never real. Their roles must be human roles. [`example-roles-and-people.json`](example-roles-and-people.json) is a complete example, which the tests use.

## Settings

| Variable | What it is | Default |
|---|---|---|
| `MOCK_IDP_CONFIG` | The path of the roles and people file in the container | None: required |
| `MOCK_IDP_ISSUER_URL` | The address the API reaches the provider on, used for the issuer and the endpoints the API calls | `http://mock-idp:9000` |
| `MOCK_IDP_BROWSER_URL` | The address the browser reaches the provider on, for the sign-in and sign-out pages | `http://localhost:9000` |
| `MOCK_IDP_DEFAULT_AUDIENCE` | The audience of test tokens when a request names none: the API's client ID | `local-internal-app` |

## Using it

The image is `ghcr.io/supermanchris4/ai-app-platform-mock-idp`, public, so it pulls with no credential. Each release is tagged with its version, such as `0.1.0`; the release notes give its digest, which an application pins as it pins every other image. In an application's Compose file:

```yaml
mock-idp:
  image: ghcr.io/supermanchris4/ai-app-platform-mock-idp:0.1.0@sha256:{digest from the release notes}
  ports:
    - "9000:9000"
  environment:
    MOCK_IDP_CONFIG: /config/mock-idp.json
  volumes:
    - ./mock-idp.json:/config/mock-idp.json:ro
```

## Developing

```bash
uv sync
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest
docker build --tag mock-idp:local .
```
