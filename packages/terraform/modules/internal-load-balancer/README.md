# internal-load-balancer

An internal Application Load Balancer, reachable only from inside the VPC, with one HTTPS listener forwarding to IP targets (Fargate tasks) (the template's 12-aws-deployment.md#compute). Access logs would need their own bucket; every request is already logged by the API, with its correlation ID, and at the edge by CloudFront and AWS WAF. nosemgrep: terraform.aws.security.aws-elb-access-logs-not-enabled.aws-elb-access-logs-not-enabled

## Usage

```hcl
module "internal_load_balancer" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/internal-load-balancer?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The load balancer's name, also used for its target group. At most 28 characters. |
| `vpc_id` | `string` | Yes | The VPC for the target group. |
| `subnet_ids` | `list(string)` | Yes | Private subnets in at least two Availability Zones. |
| `security_group_ids` | `list(string)` | Yes | The load balancer's security groups. |
| `certificate_arn` | `string` | Yes | The ACM certificate for the HTTPS listener. |
| `target_port` | `number` | Yes | The port the targets listen on. |
| `health_check_path` | `string` | Yes | The path the load balancer checks targets on. |
| `deletion_protection` | `bool` | No | Whether the load balancer is protected from deletion. |

## Outputs

| Name | Description |
|---|---|
| `arn` | The load balancer's ARN, which a CloudFront VPC origin names. |
| `dns_name` | The load balancer's DNS name. |
| `arn_suffix` | The load balancer's ARN suffix, which CloudWatch metrics name. |
| `target_group_arn` | The target group the service registers its tasks in. |
| `target_group_arn_suffix` | The target group's ARN suffix, which CloudWatch metrics name. |
