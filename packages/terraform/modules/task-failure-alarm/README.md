# task-failure-alarm

An alarm when a task of the given families fails: it stops with a non-zero exit code, or fails to start (Standard D-12). EventBridge writes each failure to a log group, which keeps a record of it, and a metric filter counts them for a CloudWatch alarm on the alarm topic.

## Usage

```hcl
module "task_failure_alarm" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/task-failure-alarm?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The prefix for the rule, log group, metric and alarm names. |
| `cluster_arn` | `string` | Yes | The cluster the tasks run in. |
| `task_definition_families` | `list(string)` | Yes | The task definition families whose failures raise the alarm. |
| `alarm_topic_arn` | `string` | Yes | The SNS topic the alarm notifies. |
| `retention_days` | `number` | Yes | Days the record of each failure is kept. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key for the failure log; null for CloudWatch's own encryption. |

## Outputs

| Name | Description |
|---|---|
| `alarm_name` | The alarm raised when a task fails. |
| `metric_namespace` | The namespace of the TaskFailures metric, for dashboards. |
