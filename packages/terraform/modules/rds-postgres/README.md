# rds-postgres

RDS for PostgreSQL (the template's 12-aws-deployment.md#database): private, encrypted at rest, TLS required, and with a master password RDS creates, keeps in Secrets Manager and rotates itself, so no password passes through Terraform or its state.

## Usage

```hcl
module "rds_postgres" {
  source = "git::https://github.com/supermanchris4/ai-app-platform.git//packages/terraform/modules/rds-postgres?ref=terraform-v{version}"

  # The required inputs below
}
```

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `identifier` | `string` | Yes | The database instance's identifier. |
| `database_name` | `string` | Yes | The database created in the instance. |
| `engine_version` | `string` | No | The PostgreSQL major version (Standard configuration default C-02). |
| `instance_class` | `string` | Yes | The instance class. |
| `allocated_storage` | `number` | Yes | Storage in GiB. |
| `multi_az` | `bool` | No | Whether the instance has a standby in another Availability Zone. |
| `subnet_ids` | `list(string)` | Yes | Private subnets in at least two Availability Zones. |
| `security_group_ids` | `list(string)` | Yes | The database's security groups. |
| `backup_retention_days` | `number` | Yes | Days of automated backups. |
| `deletion_protection` | `bool` | No | Whether the instance is protected from deletion; a final snapshot is also kept when true. Set it to false only for an environment whose data may be lost. |
| `kms_key_arn` | `string` | No | A customer-managed KMS key for storage, Performance Insights and the master password; null for AWS-managed keys. |
| `master_username` | `string` | No | The master user, used only to create the application's users. |

## Outputs

| Name | Description |
|---|---|
| `address` | The instance's host name, the API's DATABASE_HOST. |
| `port` | The instance's port. |
| `database_name` | The database's name, the API's DATABASE_NAME. |
| `identifier` | The instance's identifier, which CloudWatch metrics name. |
| `master_user_secret_arn` | The secret RDS keeps the master user's credentials in, which only the database initialisation task reads. |
