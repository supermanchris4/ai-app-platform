# scheduled-task

A scheduled job: an EventBridge Scheduler schedule that runs a task definition's latest revision on Fargate, with a role allowed only to start that task (the template's 12-aws-deployment.md#scheduled-tasks).

## Usage

```hcl
module "scheduled_task" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/scheduled-task?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The schedule's name, also used for its role. |
| `schedule_expression` | `string` | Yes | When the job runs: a cron() or rate() expression. |
| `time_zone` | `string` | Yes | The IANA time zone the cron expression is in. |
| `cluster_arn` | `string` | Yes | The cluster the job's task runs in. |
| `task_definition_family` | `string` | Yes | The job's task definition family; each run uses its latest revision, which the pipeline registers. |
| `region` | `string` | Yes | The region the task definition is in. |
| `subnet_ids` | `list(string)` | Yes | Private subnets for the job's task. |
| `security_group_ids` | `list(string)` | Yes | The job's task security groups. |
| `pass_role_arns` | `list(string)` | Yes | The task's execution and task roles, which the scheduler passes to ECS. |
| `permissions_boundary_arn` | `string` | Yes | The permissions boundary on the scheduler's role. |

## Outputs

| Name | Description |
|---|---|
| `schedule_name` | The schedule's name. |
