variable "name" {
  description = "The log group's name."
  type        = string
}

variable "retention_days" {
  description = "Days the logs are kept."
  type        = number
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key; null for CloudWatch's own encryption."
  type        = string
  default     = null
}
