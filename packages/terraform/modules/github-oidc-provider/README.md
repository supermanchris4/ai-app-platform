# github-oidc-provider

The account's GitHub Actions OIDC provider, which lets workflows assume roles with short-lived tokens instead of stored keys. An account can hold only one, so the caller creates it only where none exists (the template's 12-aws-deployment.md#account-bootstrap).

## Usage

```hcl
module "github_oidc_provider" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/github-oidc-provider?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

## Inputs

None.

## Outputs

| Name | Description |
|---|---|
| `arn` | The OIDC provider's ARN, which roles trusted by GitHub Actions name as their federated principal. |
