# resource-group

A Resource Group holding every resource that carries the given tags, so an application's resources in one environment can be found and reviewed together (the template's 12-aws-deployment.md#principles).

## Usage

```hcl
module "resource_group" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/resource-group?ref=terraform-v{version}"

  # The required inputs below
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The Resource Group's name. |
| `description` | `string` | No | What the group holds. |
| `tag_filters` | `map(string)` | Yes | The tags, by key and value, that a resource must all carry to be in the group. |

## Outputs

| Name | Description |
|---|---|
| `name` | The Resource Group's name. |
| `arn` | The Resource Group's ARN. |
