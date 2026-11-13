# github-oidc-provider

The account's GitHub Actions OIDC provider, which lets workflows assume roles with short-lived tokens instead of stored keys. An account can hold only one, so the caller creates it only where none exists (the template's 12-aws-deployment.md#account-bootstrap).

## Usage

```hcl
module "github_oidc_provider" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/github-oidc-provider?ref=terraform-v{version}"

  # The required inputs below
}
```

## Inputs

None.

## Outputs

| Name | Description |
|---|---|
| `arn` | The OIDC provider's ARN, which roles trusted by GitHub Actions name as their federated principal. |
