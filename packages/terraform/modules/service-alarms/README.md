# service-alarms

The alarms for a web service on ECS behind a load balancer (the template's 12-aws-deployment.md#monitoring), from AWS's recommended set: fewer running tasks than wanted, sustained CPU or memory use, server errors and slow responses. Each notifies the topic when it fires and when it clears.

## Usage

```hcl
module "service_alarms" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/service-alarms?ref=terraform-v{version}"

  # The required inputs below
}
```

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The prefix for the alarms' names. |
| `cluster_name` | `string` | Yes | The service's ECS cluster. |
| `service_name` | `string` | Yes | The ECS service. |
| `desired_count` | `number` | Yes | The number of tasks the service should run. |
| `load_balancer_arn_suffix` | `string` | Yes | The load balancer's ARN suffix, as CloudWatch names it. |
| `target_group_arn_suffix` | `string` | Yes | The service's target group ARN suffix, as CloudWatch names it. |
| `alarm_topic_arn` | `string` | Yes | The SNS topic the alarms notify, when they fire and when they clear. |
| `utilisation_percent` | `number` | No | CPU and memory use, as a percentage, that raises an alarm after 15 minutes. |
| `server_errors` | `number` | No | Responses with a 5xx status from the service in 5 minutes that raise an alarm. |
| `response_time_seconds` | `number` | Yes | The p95 response time, in seconds, that raises an alarm after 15 minutes. |

## Outputs

| Name | Description |
|---|---|
| `alarm_names` | The service's alarms, by what they watch. |
