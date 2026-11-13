# minimal-network

A minimal network for an account with none, shared by the applications in it: one VPC with an internet gateway attached (CloudFront VPC origins need one; nothing routes inbound through it), two private subnets in different Availability Zones, and one NAT gateway for outbound traffic (the template's 12-aws-deployment.md#account-bootstrap, Standard D-05).

## Usage

```hcl
module "minimal_network" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/minimal-network?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The prefix for the network's resource names. |
| `cidr_block` | `string` | No | The VPC's address range. A /16 to /24; the subnets are carved from it. |
| `availability_zones` | `list(string)` | Yes | The two Availability Zones for the private subnets. |
| `flow_log_retention_days` | `number` | No | Days CloudWatch keeps the VPC's flow logs. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key for the flow logs; null for CloudWatch's own encryption. |
| `permissions_boundary_arn` | `string` | Yes | The permissions boundary on the role that writes flow logs. |

## Outputs

| Name | Description |
|---|---|
| `vpc_id` | The VPC, given to each application's configuration as vpc_id. |
| `private_subnet_ids` | The two private subnets, given to each application as app_subnet_ids and lb_subnet_ids. |
