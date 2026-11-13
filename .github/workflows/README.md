# ai-app-platform: the reusable workflows

The GitHub Actions workflows an application's pipelines call, for the pull request checks, the Terraform checks, plan and apply, and the application's build and deployment, as the template's `13-delivery-pipeline.md` specifies. Each holds nothing of one application and takes its values as inputs. The application keeps only the workflows that call them: its `ci.yml`, its infrastructure plan and apply, and its deployment.

The other files here, `ci.yml` and `release.yml`, are this repository's own pipelines, which call the same workflows.

## Calling a workflow

`{platform-owner}` stands for the owner of this repository, in lower case ([README](../../README.md#packages)).

An application calls a workflow at a release, pinned by the commit SHA the release tag names, with the tag in a comment, as the template requires of every third-party action:

```yaml
jobs:
  api:
    name: API
    permissions:
      contents: read
    uses: {platform-owner}/ai-app-platform/.github/workflows/python-checks.yml@{commit SHA} # workflows-v{version}
    with:
      working-directory: apps/api
```

A reusable workflow's jobs can have no more permission than its caller grants, so the calling job grants at least the permissions each workflow lists below.

Each release is a git tag, `workflows-v{version}`, and its GitHub release names the commit the tag points to. Every call in an application uses the same release. Take the commit from the release's notes, or from this repository:

```bash
git ls-remote https://github.com/{platform-owner}/ai-app-platform 'refs/tags/workflows-v0.1.0^{}' refs/tags/workflows-v0.1.0
```

Use the line ending `^{}` if there is one (an annotated tag), and otherwise the other line. Never take a commit from a link, a pull request or a fork: GitHub serves a commit pushed to any fork of a public repository through this repository's address too, so only the release tag shows that a commit is a release.

To upgrade, read the [changelog](CHANGELOG.md) from the current version to the new one, since a major version can need a further permission, input or Terraform output, then change the SHA and the comment in every call together.

### GitHub Environments

A job that calls a reusable workflow cannot name a GitHub Environment itself, so `terraform-plan`, `terraform-apply`, `build-application` and `deploy-application` take it as the `github-environment` input, and run their job in it. Leave it empty, as by default, where the repository has no environments (on a private repository under GitHub Free, for example).

- **Protection rules.** A job in an environment waits for its required reviewers and is refused on a branch the environment does not allow. A plan on a pull request is usually run with no environment, so that it does not wait for approval.
- **The role's trust.** In an environment, the OIDC token's subject names the environment instead of the branch, so a role that trusts an environment is assumed only with `github-environment` set to it, and a role that trusts a branch only with it empty.
- **Variables.** The calling job has no environment, so its `with:` values cannot read an environment's variables. Pass repository variables, named for the environment where they differ, such as `vars.TEST_DEPLOY_ROLE_ARN`.

## Workflows

| Workflow | What it does |
|---|---|
| [`python-checks`](#python-checks) | Checks a Python project managed by uv: Ruff lint and format check, Pyright, and its tests (the template's 13-delivery-pipeline.md) |
| [`web-checks`](#web-checks) | Checks a Node web interface: lint and format check, type check, unit tests and build, then its end-to-end journeys and accessibility checks against a stack started on the runner (the template's 13-delivery-pipeline.md) |
| [`contract-check`](#contract-check) | Fails when the OpenAPI document generated from the API differs from the one committed beside the web client, or the client's generated types differ from that document (the template's 13-delivery-pipeline.md) |
| [`traceability-check`](#traceability-check) | Fails when a requirement ID that a specification section or a test cites is not a requirement, when a test names no requirement it verifies, or when the committed requirements trace report is not current (the template's 13-delivery-pipeline.md) |
| [`image-checks`](#image-checks) | Builds a container image and, when asked, scans it with Trivy, failing on high or critical vulnerabilities that have a fix (the template's 13-delivery-pipeline.md) |
| [`security-checks`](#security-checks) | Secret, code and dependency scanning with open-source tools, run from their images pinned by digest (the template's 13-delivery-pipeline.md) |
| [`terraform-checks`](#terraform-checks) | Checks Terraform: format, validation and tests with mocked providers for each configuration, then Trivy's misconfiguration scan (the template's 13-delivery-pipeline.md) |
| [`terraform-plan`](#terraform-plan) | Plans a Terraform configuration for one environment with a read-only role, and posts the plan to the pull request (the template's 13-delivery-pipeline.md) |
| [`terraform-apply`](#terraform-apply) | Applies a Terraform configuration to one environment with the deploy role (the template's 13-delivery-pipeline.md) |
| [`build-application`](#build-application) | Builds the application once (the template's 13-delivery-pipeline.md): the API image, tagged with the commit SHA and pushed to the first environment's repository, and the web build |
| [`deploy-application`](#deploy-application) | Deploys a build to one environment (the template's 13-delivery-pipeline.md): copies the image into the environment's repository if it is not there, registers new revisions of every task definition with the image and the application's settings, initialises the database users and runs the migrations, updates the API service, uploads the web build, and checks the health endpoint through CloudFront |
| [`workflow-checks`](#workflow-checks) | Checks GitHub Actions workflows with actionlint: syntax, expressions, inputs and outputs of reusable workflows, permissions, and the shell in each run step, with shellcheck |

### python-checks

Checks a Python project managed by uv: Ruff lint and format check, Pyright, and its tests (the template's 13-delivery-pipeline.md).

**Caller grants:** `contents: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `working-directory` | Yes |  | The project directory, holding pyproject.toml and uv.lock |
| `test-command` | No | `uv run pytest` | The command that runs the tests, from the project directory |
| `postgres-image` | No |  | A PostgreSQL image, pinned by digest, to run the tests against; empty for none |
| `postgres-setup-sql` | No |  | A psql script, from the repository root, run as the superuser to create the users and test database |
| `database-prefix` | No | `ci` | The prefix the setup script names the users and test database from |


### web-checks

Checks a Node web interface: lint and format check, type check, unit tests and build, then its end-to-end journeys and accessibility checks against a stack started on the runner (the template's 13-delivery-pipeline.md).

**Caller grants:** `contents: read`, `packages: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `github-packages-scope` | No |  | An npm scope whose packages come from GitHub Packages, such as "@example", read with the run's own token; empty for none |
| `working-directory` | Yes |  | The web interface's directory, holding package.json and package-lock.json |
| `lint-command` | No | `npm run lint` | The command that lints and checks formatting |
| `typecheck-command` | No | `npm run typecheck` | The command that type checks |
| `test-command` | No | `npm test` | The command that runs the unit tests |
| `build-command` | No | `npm run build` | The command that builds the app |
| `e2e-stack-command` | No |  | The command that starts the stack the end-to-end tests run against; empty for no end-to-end tests |
| `e2e-command` | No | `npx playwright test` | The command that runs the end-to-end tests |


### contract-check

Fails when the OpenAPI document generated from the API differs from the one committed beside the web client, or the client's generated types differ from that document (the template's 13-delivery-pipeline.md).

**Caller grants:** `contents: read`, `packages: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `github-packages-scope` | No |  | An npm scope whose packages come from GitHub Packages, such as "@example", read with the run's own token; empty for none |
| `api-directory` | Yes |  | The API's directory, holding pyproject.toml and uv.lock |
| `web-directory` | Yes |  | The web client's directory, holding package.json and package-lock.json |
| `command` | No | `npm run check-api` | The command, run from the web client's directory, that fails when the document or types differ |


### traceability-check

Fails when a requirement ID that a specification section or a test cites is not a requirement, when a test names no requirement it verifies, or when the committed requirements trace report is not current (the template's 13-delivery-pipeline.md). It runs `python -m ai_app_platform.traceability` from the API platform package at the version the API's `uv.lock` pins, so the API must use version 0.2.0 or later. `--write` regenerates the report locally.

**Caller grants:** `contents: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `api-directory` | Yes |  | The API's directory, holding pyproject.toml and the uv.lock that pins the API platform package |
| `arguments` | No |  | Arguments for python -m ai_app_platform.traceability, such as --report or --tests; empty for its defaults |


### image-checks

Builds a container image and, when asked, scans it with Trivy, failing on high or critical vulnerabilities that have a fix (the template's 13-delivery-pipeline.md).

**Caller grants:** `contents: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `context` | No | `.` | The build context, from the repository root |
| `dockerfile` | Yes |  | The Dockerfile, from the repository root |
| `scan` | No | `True` | Whether to scan the built image |
| `trivy-image` | No | pinned image | The Trivy image, pinned by digest |


### security-checks

Secret, code and dependency scanning with open-source tools, run from their images pinned by digest (the template's 13-delivery-pipeline.md).

**Caller grants:** `contents: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `lockfiles` | No |  | The lock files to scan for known vulnerabilities, one per line, from the repository root; empty to skip |
| `semgrep-config` | No | `p/default` | The Semgrep rulesets, separated by spaces |
| `gitleaks-image` | No | pinned image | The gitleaks image, pinned by digest |
| `semgrep-image` | No | pinned image | The Semgrep image, pinned by digest |
| `osv-scanner-image` | No | pinned image | The OSV-Scanner image, pinned by digest |


### terraform-checks

Checks Terraform: format, validation and tests with mocked providers for each configuration, then Trivy's misconfiguration scan (the template's 13-delivery-pipeline.md). Nothing is planned against or applied to an AWS account, and no credentials are used.

**Caller grants:** `contents: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `root` | Yes |  | The directory holding all the Terraform, checked for format recursively |
| `configurations` | Yes |  | The configurations and modules to validate and test, one per line; shell globs are expanded |
| `scan-path` | No | `.` | The directory Trivy scans for misconfigurations |
| `scan-skip-dirs` | No |  | Directories Trivy skips, one per line, from scan-path |
| `terraform-image` | No | pinned image | The Terraform image, pinned by digest |
| `trivy-image` | No | pinned image | The Trivy image, pinned by digest |


### terraform-plan

Plans a Terraform configuration for one environment with a read-only role, and posts the plan to the pull request (the template's 13-delivery-pipeline.md). The state lock is not taken, so the role needs only to read.

**Caller grants:** `contents: read`, `id-token: write`, `pull-requests: write`.

| Input | Required | Default | Description |
|---|---|---|---|
| `environment` | Yes |  | The environment planned, for the plan's heading |
| `github-environment` | No |  | The GitHub Environment the job runs in, for its protection rules and the role's OIDC trust; empty for none, on a plan without environments |
| `working-directory` | Yes |  | The root Terraform configuration |
| `aws-region` | Yes |  | The region of the state bucket and the deployment |
| `role-arn` | Yes |  | The read-only role to assume through OIDC |
| `state-bucket` | Yes |  | The Terraform state bucket |
| `state-key` | Yes |  | The environment's state file in the bucket |
| `tfvars-json` | Yes |  | The environment's Terraform inputs, as JSON; none is secret |
| `terraform-image` | No | pinned image | The Terraform image, pinned by digest |


### terraform-apply

Applies a Terraform configuration to one environment with the deploy role (the template's 13-delivery-pipeline.md). The plan applied is the one shown in the log, made in the same job.

**Caller grants:** `contents: read`, `id-token: write`.

| Input | Required | Default | Description |
|---|---|---|---|
| `environment` | Yes |  | The environment applied to |
| `github-environment` | No |  | The GitHub Environment the job runs in, for its protection rules and the role's OIDC trust; empty for none, on a plan without environments |
| `working-directory` | Yes |  | The root Terraform configuration |
| `aws-region` | Yes |  | The region of the state bucket and the deployment |
| `role-arn` | Yes |  | The deploy role to assume through OIDC |
| `state-bucket` | Yes |  | The Terraform state bucket |
| `state-key` | Yes |  | The environment's state file in the bucket |
| `tfvars-json` | Yes |  | The environment's Terraform inputs, as JSON; none is secret |
| `terraform-image` | No | pinned image | The Terraform image, pinned by digest |


### build-application

Builds the application once (the template's 13-delivery-pipeline.md): the API image, tagged with the commit SHA and pushed to the first environment's repository, and the web build. Both are kept as one artifact, "release", which every later deployment of this build uses: the web build, and image.txt naming the image by digest.

**Caller grants:** `contents: read`, `id-token: write`, `packages: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `github-packages-scope` | No |  | An npm scope whose packages come from GitHub Packages, such as "@example", read with the run's own token; empty for none |
| `environment` | Yes |  | The environment whose image repository receives the build |
| `github-environment` | No |  | The GitHub Environment the job runs in, for its protection rules and the role's OIDC trust; empty for none, on a plan without environments |
| `infra-directory` | Yes |  | The root Terraform configuration, whose ecr_repository_url output names the repository |
| `aws-region` | Yes |  | The environment's region |
| `role-arn` | Yes |  | The deploy role to assume through OIDC |
| `state-bucket` | Yes |  | The Terraform state bucket |
| `state-key` | Yes |  | The environment's state file in the bucket |
| `api-context` | No | `.` | The API image's build context |
| `api-dockerfile` | Yes |  | The API image's Dockerfile |
| `web-directory` | Yes |  | The web interface, built with npm run build into dist/ |
| `terraform-image` | No | pinned image | The Terraform image, pinned by digest |

| Output | Description |
|---|---|
| `image` | The API image, by digest |


### deploy-application

Deploys a build to one environment (the template's 13-delivery-pipeline.md): copies the image into the environment's repository if it is not there, registers new revisions of every task definition with the image and the application's settings, initialises the database users and runs the migrations, updates the API service, uploads the web build, and checks the health endpoint through CloudFront.

**Caller grants:** `actions: read`, `contents: read`, `id-token: write`.

| Input | Required | Default | Description |
|---|---|---|---|
| `environment` | Yes |  | The environment deployed to |
| `github-environment` | No |  | The GitHub Environment the job runs in, for its protection rules and the role's OIDC trust; empty for none, on a plan without environments |
| `infra-directory` | Yes |  | The root Terraform configuration, whose outputs name the environment's resources |
| `aws-region` | Yes |  | The environment's region |
| `role-arn` | Yes |  | The deploy role to assume through OIDC |
| `state-bucket` | Yes |  | The Terraform state bucket |
| `state-key` | Yes |  | The environment's state file in the bucket |
| `build-run-id` | No |  | The run that built the release to deploy; empty for this run |
| `app-settings-json` | Yes |  | The application's settings for this environment, as a JSON object of names and values; none is secret |
| `health-path` | No | `/api/health` | The path checked through CloudFront after deploying |
| `terraform-image` | No | pinned image | The Terraform image, pinned by digest |

### workflow-checks

Checks GitHub Actions workflows with actionlint: syntax, expressions, inputs and outputs of reusable workflows, permissions, and the shell in each run step, with shellcheck. Run from its image pinned by digest.

**Caller grants:** `contents: read`.

| Input | Required | Default | Description |
|---|---|---|---|
| `actionlint-image` | No | pinned image | The actionlint image, pinned by digest |

## The Terraform outputs `build-application` and `deploy-application` read

Both workflows run `terraform output -json` in the application's Terraform root (`infra-directory`) for the environment, and read these outputs. The application's root provides every one, whatever else it outputs.

| Output | Type | What the workflows do with it |
|---|---|---|
| `ecr_repository_url` | string | The API image repository: the build pushes each image there, tagged with the commit SHA, and a deployment copies the image there if it is not yet in that environment's repository |
| `ecs_cluster_name` | string | The ECS cluster the service runs in and one-off tasks run in |
| `api_service_name` | string | The API's ECS service, updated to each new revision and waited on until stable |
| `api_task_family` | string | The API's task definition family |
| `migration_task_family` | string | The migration task's family, run to completion before each deployment |
| `database_init_task_family` | string | The database initialisation task's family, run to completion before the migrations; it must be safe to run on every deployment |
| `job_task_families` | list of strings | Each scheduled job's task definition family |
| `task_subnet_ids` | list of strings | The subnets one-off tasks run in |
| `task_security_group_id` | string | The security group one-off tasks run with |
| `web_bucket_name` | string | The bucket each web build is uploaded to |
| `cloudfront_distribution_id` | string | The distribution invalidated after an upload |
| `public_url` | string | The address people use; `/api/health` (or `health-path`) is checked through it after a deployment |

**Task definitions.** Terraform creates the first revision of each family; `deploy-application` registers the next ones. Each new revision starts from the latest, keeps its roles, network mode, CPU, memory and platform, and sets every container's image to the build's. Except for the database initialisation task, each container's environment is the latest revision's, overlaid with `app-settings-json` and `APP_VERSION` set to the commit SHA. No setting in `app-settings-json` is secret. Secrets reach a container either through the task definition's `secrets`, from Secrets Manager, which each new revision keeps, or as a Secrets Manager ARN in its settings, which the API reads at run time.

## Changing a workflow

An input, an output, a permission and the Terraform outputs above are what applications rely on. Adding an optional input or an output is a minor version; removing or renaming one, adding a required input, needing a further permission, or reading a further Terraform output is a major version, noted in the [changelog](CHANGELOG.md).
