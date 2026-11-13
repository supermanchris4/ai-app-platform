# secret

A Secrets Manager secret created without a value: whatever sets the value (a task, an operator or a rotation) does so outside Terraform, so no secret value is in code or state (Standard D-13). A customer-managed key is optional (AWS-0098); without one, the AWS-managed key is used.

## Usage

```hcl
module "secret" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/secret?ref=terraform-v{version}"

  # The required inputs below
}
```

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The secret's name. |
| `description` | `string` | Yes | What the secret holds. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key; null for Secrets Manager's AWS-managed key. |
| `recovery_window_days` | `number` | No | Days a deleted secret can be restored; 0 deletes it at once. |
| `rotation_function_arn` | `string` | No | The Lambda function that rotates the secret; null for no rotation. |
| `rotation_days` | `number` | No | Days between rotations, when rotation_function_arn is set. |
| `rotate` | `bool` | No | Whether rotation is on. Known at plan time, unlike rotation_function_arn. |

## Outputs

| Name | Description |
|---|---|
| `arn` | The secret's ARN. |
| `name` | The secret's name. |
