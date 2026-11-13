variable "name" {
  description = "The bucket's name, unique across AWS."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.name))
    error_message = "name must be a valid S3 bucket name."
  }
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key to encrypt state with; null for S3-managed keys."
  type        = string
  default     = null
}

variable "noncurrent_version_days" {
  description = "Days an earlier version of a state file is kept, so a bad change can be undone."
  type        = number
  default     = 90

  validation {
    condition     = var.noncurrent_version_days >= 1
    error_message = "noncurrent_version_days must be at least 1."
  }
}
