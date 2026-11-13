# ecs-cluster

An ECS cluster with Container Insights, for the service, one-off tasks and scheduled jobs.

## Usage

```hcl
module "ecs_cluster" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/ecs-cluster?ref=terraform-v{version}"

  # The required inputs below
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The cluster's name. |

## Outputs

| Name | Description |
|---|---|
| `name` | The cluster's name. |
| `arn` | The cluster's ARN. |
