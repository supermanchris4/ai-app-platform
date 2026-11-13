# ai-app-platform

The shared platform code for applications built from the AI application template (`ai-app-template`), following the AI application standard (`ai-app-standard`): what every application needs and none should write again.

Applications install the packages by version tag. The code was built first inside the first application built to the standard, and moved here once its boundaries were settled (the standard's work plan, Feature F03.2).

## Packages

| Package | Folder | What it is | Released as |
|---|---|---|---|
| API platform | `packages/api` | Settings, logging, database access, middleware, health, sign-in and access, and audit, for a FastAPI application | A git tag, `api-v{version}`, installed by uv from the tag and the folder |
| Web platform | `packages/web` | The web shell's platform code for a React application: the API client (CSRF token and correlation ID on every request), the session provider and route guard, sign-in navigation, the error notice, the environment banner, `config.json`, local dates and navigation links | `@supermanchris4/ai-app-platform-web` in GitHub Packages, tag `web-v{version}` |
| Mock identity provider | `packages/mock-idp` | A local OpenID Connect provider standing in for the internal issuer, configured with each application's roles and synthetic people | `ghcr.io/supermanchris4/ai-app-platform-mock-idp`, tag `mock-idp-v{version}` |
| Terraform modules | `packages/terraform` | The Terraform modules an application's infrastructure is built from, one per concern in the template's `12-aws-deployment.md` | A git tag, `terraform-v{version}`, used as each module's git source at the commit it names |
| Reusable workflows | `.github/workflows` | The pull request checks, Terraform checks, plan and apply, and the application build and deployment, called by an application's pipelines | A git tag, `workflows-v{version}`, called at the commit it names |

Each package implements the template specifications it names, and its tests show they are met. Each package's README says how to install it, and its CHANGELOG what each version changed. The workflows' README and CHANGELOG are in `.github/workflows`.

## Releasing

A package is released by pushing its version tag from `main`, which runs [`release.yml`](.github/workflows/release.yml):

1. In a pull request, set the package's new version (`pyproject.toml` or `package.json`) and add its entry to the package's `CHANGELOG.md`. A change an application would notice is noted there; a breaking change is a new major version. The Terraform modules and the workflows have no version file: their version is the newest entry in their `CHANGELOG.md`.
2. Once it is merged, tag the merge commit and push the tag:

   ```bash
   git switch main && git pull
   git tag api-v0.2.0   # or web-v…, mock-idp-v…, terraform-v… or workflows-v…
   git push origin api-v0.2.0
   ```

The workflow refuses a tag whose version differs from the package's, which is not on `main`, or which has no changelog entry. It runs the package's checks again, publishes it, and creates the GitHub release.

Release tags cannot be moved or deleted once pushed ([`release-tags.json`](.github/rulesets/release-tags.json)), and a published release cannot be changed (the repository's release immutability), since applications install by the tag or the commit it names. A tag that fails its checks is left in place, and the fix is released as the next version.

## Repository settings

The repository's rulesets are kept in [`.github/rulesets`](.github/rulesets), so a change to one is reviewed in a pull request like any other. GitHub does not read these files: once the change is merged, an administrator applies it from `main` (`gh` fills in `{owner}` and `{repo}` from the clone):

```bash
git switch main && git pull
gh api repos/{owner}/{repo}/rulesets --jq '.[] | "\(.id) \(.name)"'   # the live rulesets and their IDs
gh api -X PUT repos/{owner}/{repo}/rulesets/ID --input .github/rulesets/main.json   # change an existing one, by its ID
gh api -X POST repos/{owner}/{repo}/rulesets --input .github/rulesets/release-tags.json   # create a new one
```

| Ruleset | What it does |
|---|---|
| [`main.json`](.github/rulesets/main.json) | Changes reach `main` only by pull request, after the checks in `ci.yml` pass; `main` cannot be deleted or force-pushed |
| [`release-tags.json`](.github/rulesets/release-tags.json) | Release tags cannot be moved or deleted, by anyone |

A check added to `ci.yml` is added to `main.json`'s required checks in the same pull request, and applied once merged.

The other settings, which have no file, are set by an administrator:

| Setting | Where | Value |
|---|---|---|
| Release immutability | Settings → General → Releases | On |
| Approval for fork pull request workflows | Settings → Actions → General | Require approval for all external contributors |
| Require actions to be pinned to a full-length commit SHA | Settings → Actions → General | On |
| Workflow permissions | Settings → Actions → General | Read repository contents and packages permissions |
| Secret scanning and push protection | Settings → Advanced Security | On |
| Dependabot security updates | Settings → Advanced Security | On |

## Contributing

Every change is a pull request to `main`, which needs the checks in [`ci.yml`](.github/workflows/ci.yml) to pass. Before committing, install the secret scan once per clone: `pre-commit install`.

## Licence

Apache License 2.0: see [LICENSE](LICENSE).
