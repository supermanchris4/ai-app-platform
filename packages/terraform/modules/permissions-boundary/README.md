# permissions-boundary

A permissions boundary for every role an application's pipelines create or use. It allows the listed services, and IAM only to manage the application's own roles, each of which must carry this same boundary; nothing under it can remove or change the boundary, or change the protected roles. The policy document is also the deploy role's own permissions (see outputs).

## Usage

```hcl
module "permissions_boundary" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/permissions-boundary?ref=terraform-v{version}"

  # The required inputs below
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The boundary policy's name. |
| `allowed_services` | `list(string)` | Yes | The AWS service prefixes roles under the boundary may use, such as ecs or s3. |
| `role_name_prefix` | `string` | Yes | Roles may create, change, pass and delete only roles whose names start with this, and only with this boundary. |
| `protected_role_names` | `list(string)` | No | Roles no role under the boundary may change, such as the pipeline roles themselves. |

## Outputs

| Name | Description |
|---|---|
| `arn` | The boundary policy's ARN, set as permissions_boundary_arn on every role. |
| `document` | The boundary's policy document, in JSON: the most a role under it can do, and so the deploy role's own permissions. |
