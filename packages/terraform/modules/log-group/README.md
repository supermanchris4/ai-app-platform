# log-group

A CloudWatch log group with a retention period. A customer-managed key is optional (AWS-0017); without one, CloudWatch encrypts logs with its own key.

## Usage

```hcl
module "log_group" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/log-group?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The log group's name. |
| `retention_days` | `number` | Yes | Days the logs are kept. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key; null for CloudWatch's own encryption. |

## Outputs

| Name | Description |
|---|---|
| `name` | The log group's name. |
| `arn` | The log group's ARN. |
