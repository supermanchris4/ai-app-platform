# ecs-cluster

An ECS cluster with Container Insights, for the service, one-off tasks and scheduled jobs.

## Usage

```hcl
module "ecs_cluster" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/ecs-cluster?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The cluster's name. |

## Outputs

| Name | Description |
|---|---|
| `name` | The cluster's name. |
| `arn` | The cluster's ARN. |
