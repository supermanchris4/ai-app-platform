# terraform-state-bucket

The bucket holding Terraform state, with S3's native state locking (no DynamoDB table): versioned, encrypted, private and reachable only over TLS (the template's 12-aws-deployment.md#account-bootstrap). Access logging would need a second bucket (AWS-0089); CloudTrail records who changes state.

## Usage

```hcl
module "terraform_state_bucket" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/terraform-state-bucket?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The bucket's name, unique across AWS. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key to encrypt state with; null for S3-managed keys. |
| `noncurrent_version_days` | `number` | No | Days an earlier version of a state file is kept, so a bad change can be undone. |

## Outputs

| Name | Description |
|---|---|
| `name` | The bucket's name, given to terraform init as the backend's bucket. |
| `arn` | The bucket's ARN. |
