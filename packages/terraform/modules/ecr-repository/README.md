# ecr-repository

An image repository: tags are immutable, so a tag always names the same build; every image is scanned when pushed; old images expire (the template's 12-aws-deployment.md#compute). A customer-managed key is optional (AWS-0033); without one, ECR encrypts with an AWS-managed key.

## Usage

```hcl
module "ecr_repository" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/ecr-repository?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The repository's name. |
| `keep_images` | `number` | No | How many of the most recent images to keep; older ones are expired. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key; null for AWS-managed encryption. |

## Outputs

| Name | Description |
|---|---|
| `url` | The repository's URL, to tag and push images to. |
| `arn` | The repository's ARN. |
| `name` | The repository's name. |
