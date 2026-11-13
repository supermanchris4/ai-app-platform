# private-bucket

A private S3 bucket: encrypted, public access blocked, owner-enforced, reachable only over TLS, with an optional expiry for its objects. Access logging would need another bucket (AWS-0089), and a customer-managed key is optional (AWS-0132).

## Usage

```hcl
module "private_bucket" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/private-bucket?ref=terraform-v{version}"

  # The required inputs below
}
```

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The bucket's name, unique across AWS. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key; null for S3-managed keys. |
| `versioning` | `bool` | No | Whether the bucket keeps earlier versions of objects. |
| `policy_documents` | `list(string)` | No | Further bucket policy documents, in JSON, merged with the TLS-only rule; for example a CloudFront read grant. |
| `expire_after_days` | `number` | No | Days after which objects are deleted; null to keep them. |

## Outputs

| Name | Description |
|---|---|
| `name` | The bucket's name. |
| `regional_domain_name` | The bucket's regional domain name, which a CloudFront origin names. |
| `arn` | The bucket's ARN. |
