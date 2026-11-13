# service-security-groups

The three security groups of a web service (the template's 12-aws-deployment.md#network-and-security-groups):  load balancer  in: HTTPS from CloudFront only     out: the tasks on the container port tasks          in: the container port from the LB  out: the database; HTTPS to AWS and issuers database       in: its port from the tasks only    out: none

## Usage

```hcl
module "service_security_groups" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/service-security-groups?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The prefix for the security groups' names. |
| `vpc_id` | `string` | Yes | The VPC the groups belong to. |
| `container_port` | `number` | Yes | The port the service's tasks listen on. |
| `database_port` | `number` | No | The database's port. |
| `load_balancer_source_prefix_list` | `string` | No | The managed prefix list allowed to reach the load balancer on HTTPS; by default CloudFront's origin-facing addresses. |

## Outputs

| Name | Description |
|---|---|
| `load_balancer_id` | The load balancer's security group. |
| `tasks_id` | The security group for the service's tasks, including one-off and scheduled tasks. |
| `database_id` | The database's security group. |
