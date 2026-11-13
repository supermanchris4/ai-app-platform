variable "name" {
  description = "The repository's name."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]+([._/-][a-z0-9]+)*$", var.name))
    error_message = "name must be a valid ECR repository name."
  }
}

variable "keep_images" {
  description = "How many of the most recent images to keep; older ones are expired."
  type        = number
  default     = 30

  validation {
    condition     = var.keep_images >= 1
    error_message = "keep_images must be at least 1."
  }
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key; null for AWS-managed encryption."
  type        = string
  default     = null
}
