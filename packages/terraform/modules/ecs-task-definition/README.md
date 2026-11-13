# ecs-task-definition

A Fargate task definition with one container, logging to CloudWatch. The deployment pipeline registers later revisions with each build's image digest and the application's settings, so the revision Terraform creates is only the first (the template's 12-aws-deployment.md#compute).

## Usage

```hcl
module "ecs_task_definition" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/ecs-task-definition?ref=terraform-v{version}"

  # The required inputs below
}
```

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `family` | `string` | Yes | The task definition's family. |
| `container_name` | `string` | No | The container's name. |
| `image` | `string` | Yes | The image the first revision runs. Later revisions are registered by the deployment pipeline with each build's digest. |
| `cpu` | `number` | Yes | CPU units for the task. |
| `memory` | `number` | Yes | Memory in MiB for the task. |
| `command` | `list(string)` | No | The command to run instead of the image's default; null for the default. |
| `container_port` | `number` | No | The port the container listens on; null for a task that serves nothing. |
| `health_check_command` | `list(string)` | No | The container health check's command, run in the container; null for none. |
| `environment` | `map(string)` | No | Settings given to the container, by name. None may be secret. |
| `secrets` | `map(string)` | No | Settings read from Secrets Manager at start-up, by name: each value is a secret's ARN, optionally with a JSON key (arn:...:key::). |
| `execution_role_arn` | `string` | Yes | The role ECS uses to pull the image, write logs and read the secrets. |
| `task_role_arn` | `string` | Yes | The role the application runs as. |
| `log_group_name` | `string` | Yes | The CloudWatch log group the container writes to. |
| `region` | `string` | Yes | The log group's region. |

## Outputs

| Name | Description |
|---|---|
| `arn` | The revision's ARN. |
| `family` | The task definition's family, which the pipeline registers new revisions in. |
| `container_name` | The container's name. |
