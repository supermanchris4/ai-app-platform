# ai-app-platform

The shared platform code for applications built from the [AI application template](https://github.com/supermanchris4/ai-app-template), following the [AI application standard](https://github.com/supermanchris4/ai-app-standard): what every application needs and none should write again.

Applications install the packages by version tag. The code was built first inside the first application, identity-spine, and moved here once its boundaries were settled (the standard's work plan, Feature F03.2).

## Packages

| Package | Folder | What it is | Released as |
|---|---|---|---|
| API platform | `packages/api` | Settings, logging, database access, middleware, health, sign-in and access, and audit, for a FastAPI application | A git tag, `api-v{version}`, installed by uv from the tag and the folder |
| Web platform | `packages/web` | The web shell's platform code for a React application: the API client (CSRF token and correlation ID on every request), the session provider and route guard, sign-in navigation, the error notice, the environment banner, `config.json`, local dates and navigation links | `@supermanchris4/ai-app-platform-web` in GitHub Packages, tag `web-v{version}` |
| Mock identity provider | `packages/mock-idp` | A local OpenID Connect provider standing in for the internal issuer, configured with each application's roles and synthetic people | `ghcr.io/supermanchris4/ai-app-platform-mock-idp`, tag `mock-idp-v{version}` |

Each package implements the template specifications it names, and its tests show they are met. Being moved in now; how to install each is added with the first release.

Terraform modules and reusable workflows join later (the standard's Feature F03.3).

## Contributing

Every change is a pull request to `main`, which needs the checks in [`ci.yml`](.github/workflows/ci.yml) to pass. Before committing, install the secret scan once per clone: `pre-commit install`.

## Licence

Apache License 2.0: see [LICENSE](LICENSE).
