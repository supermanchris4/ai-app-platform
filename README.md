# ai-app-platform

The shared platform code for applications built from the AI application template (`ai-app-template`), following the AI application standard (`ai-app-standard`): what every application needs and none should write again.

Applications install the packages by version tag. The code was built first inside the first application built to the standard, and moved here once its boundaries were settled (the standard's work plan, Feature F03.2).

## Packages

| Package | Folder | What it is | Released as |
|---|---|---|---|
| API platform | `packages/api` | Settings, logging, database access, middleware, health, sign-in and access, and audit, for a FastAPI application | A git tag, `api-v{version}`, installed by uv from the tag and the folder |
| Web platform | `packages/web` | The web shell's platform code for a React application: the API client (CSRF token and correlation ID on every request), the session provider and route guard, sign-in navigation, the error notice, the environment banner, `config.json`, local dates and navigation links | `@supermanchris4/ai-app-platform-web` in GitHub Packages, tag `web-v{version}` |
| Mock identity provider | `packages/mock-idp` | A local OpenID Connect provider standing in for the internal issuer, configured with each application's roles and synthetic people | `ghcr.io/supermanchris4/ai-app-platform-mock-idp`, tag `mock-idp-v{version}` |

Each package implements the template specifications it names, and its tests show they are met. Each package's README says how to install it, and its CHANGELOG what each version changed.

Terraform modules and reusable workflows join later (the standard's Feature F03.3).

## Releasing

A package is released by pushing its version tag from `main`, which runs [`release.yml`](.github/workflows/release.yml):

1. In a pull request, set the package's new version (`pyproject.toml` or `package.json`) and add its entry to the package's `CHANGELOG.md`. A change an application would notice is noted there; a breaking change is a new major version.
2. Once it is merged, tag the merge commit and push the tag:

   ```bash
   git switch main && git pull
   git tag api-v0.2.0   # or web-v… or mock-idp-v…
   git push origin api-v0.2.0
   ```

The workflow refuses a tag whose version differs from the package's, which is not on `main`, or which has no changelog entry. It runs the package's checks again, publishes it, and creates the GitHub release.

## Contributing

Every change is a pull request to `main`, which needs the checks in [`ci.yml`](.github/workflows/ci.yml) to pass. Before committing, install the secret scan once per clone: `pre-commit install`.

## Licence

Apache License 2.0: see [LICENSE](LICENSE).
