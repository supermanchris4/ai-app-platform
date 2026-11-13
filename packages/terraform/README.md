# ai-app-platform: the Terraform modules

The Terraform modules an application's infrastructure is built from, one per concern in the template's `12-aws-deployment.md`. An application's own Terraform roots (its deployed environment and its account bootstrap) compose them, and hold only what is the application's own: its names, its settings and any resource no other application needs.

Each module is used by its git source at a release tag, so every environment is built from the same, tested module code:

```hcl
module "database" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/rds-postgres?ref=terraform-v{version}"
  # ...
}
```

How to take a release is added with the first release. The modules need Terraform 1.16 or later and the AWS provider 6.70 or later; the application's root pins the exact versions in its lock file.

## Modules

| Module | What it is |
|---|---|
| [`cdn-distribution`](modules/cdn-distribution/README.md) | One CloudFront distribution, the application's only entry point |
| [`ecr-repository`](modules/ecr-repository/README.md) | An image repository: tags are immutable, so a tag always names the same build; every image is scanned when pushed; old images expire |
| [`ecs-cluster`](modules/ecs-cluster/README.md) | An ECS cluster with Container Insights, for the service, one-off tasks and scheduled jobs |
| [`ecs-service`](modules/ecs-service/README.md) | A Fargate service behind a load balancer, spread across Availability Zones, with no public IP addresses, and rolled back by the circuit breaker if a deployment fails |
| [`ecs-task-definition`](modules/ecs-task-definition/README.md) | A Fargate task definition with one container, logging to CloudWatch |
| [`github-actions-role`](modules/github-actions-role/README.md) | A role that GitHub Actions workflows assume through OIDC, trusted only by the exact subjects given, so no other repository, branch or environment can use it |
| [`github-oidc-provider`](modules/github-oidc-provider/README.md) | The account's GitHub Actions OIDC provider, which lets workflows assume roles with short-lived tokens instead of stored keys |
| [`internal-load-balancer`](modules/internal-load-balancer/README.md) | An internal Application Load Balancer, reachable only from inside the VPC, with one HTTPS listener forwarding to IP targets (Fargate tasks) |
| [`log-group`](modules/log-group/README.md) | A CloudWatch log group with a retention period |
| [`minimal-network`](modules/minimal-network/README.md) | A minimal network for an account with none, shared by the applications in it |
| [`permissions-boundary`](modules/permissions-boundary/README.md) | A permissions boundary for every role an application's pipelines create or use |
| [`private-bucket`](modules/private-bucket/README.md) | A private S3 bucket: encrypted, public access blocked, owner-enforced, reachable only over TLS, with an optional expiry for its objects |
| [`rds-postgres`](modules/rds-postgres/README.md) | RDS for PostgreSQL |
| [`resource-group`](modules/resource-group/README.md) | A Resource Group holding every resource that carries the given tags, so an application's resources in one environment can be found and reviewed together |
| [`rotation-function`](modules/rotation-function/README.md) | AWS's Secrets Manager single-user rotation function for PostgreSQL, installed from the Serverless Application Repository through CloudFormation, using the bootstrap's CloudFormation role |
| [`scheduled-task`](modules/scheduled-task/README.md) | A scheduled job |
| [`secret`](modules/secret/README.md) | A Secrets Manager secret created without a value |
| [`service-alarms`](modules/service-alarms/README.md) | The alarms for a web service on ECS behind a load balancer, from AWS's recommended set |
| [`service-role`](modules/service-role/README.md) | A role an AWS service assumes, such as an ECS task's execution or task role, under the permissions boundary |
| [`service-security-groups`](modules/service-security-groups/README.md) | The three security groups of a web service |
| [`task-failure-alarm`](modules/task-failure-alarm/README.md) | An alarm when a task of the given families fails: it stops with a non-zero exit code, or fails to start (Standard D-12) |
| [`terraform-state-bucket`](modules/terraform-state-bucket/README.md) | The bucket holding Terraform state, with S3's native state locking (no DynamoDB table) |
| [`web-acl`](modules/web-acl/README.md) | An AWS WAF web ACL for a CloudFront distribution |

Each module's README lists its inputs and outputs.

## Developing

The checks the pull request runs, from this folder, with the Terraform version the checks pin:

```bash
terraform fmt -check -recursive .
for dir in modules/*; do
  terraform -chdir="$dir" init -backend=false -input=false
  terraform -chdir="$dir" validate
  if [ -d "$dir/tests" ]; then terraform -chdir="$dir" test; fi
done
```

The tests run against mocked providers, with no AWS account or credentials. Trivy's misconfiguration scan runs over the folder too. Nothing here is applied to an AWS account: the modules are first applied through an application's pipeline.

Lock files are not kept for modules (`.gitignore`); each application's root keeps its own.

## Changing a module

A module's inputs, outputs and resources are what applications rely on. Adding an optional input or an output is a minor version; removing or renaming one, or changing a resource so that an application's next plan would replace it, is a major version, noted in the [changelog](CHANGELOG.md).
