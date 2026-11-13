# ecs-service

A Fargate service behind a load balancer, spread across Availability Zones, with no public IP addresses, and rolled back by the circuit breaker if a deployment fails. The pipeline owns the running task definition, so Terraform ignores later changes to it (the template's 12-aws-deployment.md#compute).

## Usage

```hcl
module "ecs_service" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/ecs-service?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The service's name. |
| `cluster_arn` | `string` | Yes | The cluster the service runs in. |
| `task_definition_arn` | `string` | Yes | The first task definition revision. Later ones are set by the deployment pipeline, and Terraform leaves them be. |
| `desired_count` | `number` | Yes | The number of tasks. |
| `subnet_ids` | `list(string)` | Yes | Private subnets for the tasks, in at least two Availability Zones. |
| `security_group_ids` | `list(string)` | Yes | The tasks' security groups. |
| `target_group_arn` | `string` | Yes | The load balancer target group the tasks register in. |
| `container_name` | `string` | Yes | The container the load balancer forwards to. |
| `container_port` | `number` | Yes | The port the load balancer forwards to. |

## Outputs

| Name | Description |
|---|---|
| `name` | The service's name. |
