variable "name" {
  description = "The secret's name."
  type        = string
}

variable "description" {
  description = "What the secret holds."
  type        = string
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key; null for Secrets Manager's AWS-managed key."
  type        = string
  default     = null
}

variable "recovery_window_days" {
  description = "Days a deleted secret can be restored; 0 deletes it at once."
  type        = number
  default     = 7
}

variable "rotation_function_arn" {
  description = "The Lambda function that rotates the secret; null for no rotation."
  type        = string
  default     = null
}

variable "rotation_days" {
  description = "Days between rotations, when rotation_function_arn is set."
  type        = number
  default     = 90
}

variable "rotate" {
  description = "Whether rotation is on. Known at plan time, unlike rotation_function_arn."
  type        = bool
  default     = false
}
