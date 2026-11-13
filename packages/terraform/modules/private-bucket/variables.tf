variable "name" {
  description = "The bucket's name, unique across AWS."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.name))
    error_message = "name must be a valid S3 bucket name."
  }
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key; null for S3-managed keys."
  type        = string
  default     = null
}

variable "versioning" {
  description = "Whether the bucket keeps earlier versions of objects."
  type        = bool
  default     = false
}

variable "policy_documents" {
  description = "Further bucket policy documents, in JSON, merged with the TLS-only rule; for example a CloudFront read grant."
  type        = list(string)
  default     = []
}

variable "expire_after_days" {
  description = "Days after which objects are deleted; null to keep them."
  type        = number
  default     = null
}
