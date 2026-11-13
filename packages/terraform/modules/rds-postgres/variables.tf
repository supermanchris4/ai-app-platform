variable "identifier" {
  description = "The database instance's identifier."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,62}$", var.identifier))
    error_message = "identifier must start with a letter and hold lower-case letters, digits or hyphens."
  }
}

variable "database_name" {
  description = "The database created in the instance."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,62}$", var.database_name))
    error_message = "database_name must start with a letter and hold lower-case letters, digits or underscores."
  }
}

variable "engine_version" {
  description = "The PostgreSQL major version (Standard configuration default C-02)."
  type        = string
  default     = "17"
}

variable "instance_class" {
  description = "The instance class."
  type        = string
}

variable "allocated_storage" {
  description = "Storage in GiB."
  type        = number
}

variable "multi_az" {
  description = "Whether the instance has a standby in another Availability Zone."
  type        = bool
  default     = false
}

variable "subnet_ids" {
  description = "Private subnets in at least two Availability Zones."
  type        = list(string)
}

variable "security_group_ids" {
  description = "The database's security groups."
  type        = list(string)
}

variable "backup_retention_days" {
  description = "Days of automated backups."
  type        = number
}

variable "deletion_protection" {
  description = "Whether the instance is protected from deletion; a final snapshot is also kept when true. Set it to false only for an environment whose data may be lost."
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key for storage, Performance Insights and the master password; null for AWS-managed keys."
  type        = string
  default     = null
}

variable "master_username" {
  description = "The master user, used only to create the application's users."
  type        = string
  default     = "dbadmin"
}
