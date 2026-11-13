# github-actions-role

A role that GitHub Actions workflows assume through OIDC, trusted only by the exact subjects given, so no other repository, branch or environment can use it.

## Usage

```hcl
module "github_actions_role" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/github-actions-role?ref=terraform-v{version}"

  # The required inputs below
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The role's name. |
| `description` | `string` | No | What the role is for. |
| `oidc_provider_arn` | `string` | Yes | The account's GitHub Actions OIDC provider. |
| `subjects` | `list(string)` | Yes | The exact OIDC subjects that may assume the role, such as repository_id:123:ref:refs/heads/main. Wildcards are not allowed. |
| `permissions_boundary_arn` | `string` | Yes | The permissions boundary on the role. |
| `managed_policy_arns` | `list(string)` | No | Managed policies attached to the role. |
| `inline_policies` | `map(string)` | No | Policy documents, in JSON, held on the role, by name. The names must be known at plan time; the documents need not be. |
| `max_session_hours` | `number` | No | The longest session a workflow can have with the role, in hours. |

## Outputs

| Name | Description |
|---|---|
| `arn` | The role's ARN, which a workflow names to assume it. |
| `name` | The role's name. |
