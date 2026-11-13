# service-role

A role an AWS service assumes, such as an ECS task's execution or task role, under the permissions boundary.

## Usage

```hcl
module "service_role" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/service-role?ref=terraform-v{version}"

  # The required inputs below
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The role's name. |
| `description` | `string` | No | What the role is for. |
| `service_principals` | `list(string)` | Yes | The AWS services that may assume the role, such as ecs-tasks.amazonaws.com. |
| `source_account` | `string` | No | The account the services must act for, guarding against the confused deputy problem; null to not check. |
| `permissions_boundary_arn` | `string` | Yes | The permissions boundary on the role. |
| `managed_policy_arns` | `list(string)` | No | Managed policies attached to the role. |
| `inline_policies` | `map(string)` | No | Policy documents, in JSON, held on the role, by name. The names must be known at plan time; the documents need not be. |

## Outputs

| Name | Description |
|---|---|
| `arn` | The role's ARN. |
| `name` | The role's name. |
