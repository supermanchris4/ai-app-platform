variable "name" {
  description = "The prefix for the stack and function names; the bootstrap's CloudFormation role may only create roles named {name}-rotation-* and the function {name}-rotation."
  type        = string
}

variable "application_id" {
  description = "The Serverless Application Repository application holding AWS's rotation function."
  type        = string
  default     = "arn:aws:serverlessrepo:us-east-1:297356227824:applications/SecretsManagerRDSPostgreSQLRotationSingleUser"
}

variable "application_version" {
  description = "The application's semantic version; null for the latest, which should then be pinned."
  type        = string
  default     = null
}

variable "cloudformation_role_arn" {
  description = "The role CloudFormation uses to install the function, from the bootstrap. See README.md."
  type        = string
}

variable "region" {
  description = "The region, for the Secrets Manager endpoint the function calls."
  type        = string
}

variable "subnet_ids" {
  description = "The private subnets the function runs in, to reach the database."
  type        = list(string)
}

variable "security_group_ids" {
  description = "The function's security groups: allowed to the database, and to HTTPS for Secrets Manager."
  type        = list(string)
}

variable "kms_key_arn" {
  description = "The customer-managed key the secrets use, if any, so the function can decrypt them."
  type        = string
  default     = null
}
