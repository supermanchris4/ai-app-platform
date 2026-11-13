variable "name" {
  description = "The prefix for the rule, log group, metric and alarm names."
  type        = string
}

variable "cluster_arn" {
  description = "The cluster the tasks run in."
  type        = string
}

variable "task_definition_families" {
  description = "The task definition families whose failures raise the alarm."
  type        = list(string)

  validation {
    condition     = length(var.task_definition_families) > 0
    error_message = "task_definition_families must name at least one family."
  }
}

variable "alarm_topic_arn" {
  description = "The SNS topic the alarm notifies."
  type        = string
}

variable "retention_days" {
  description = "Days the record of each failure is kept."
  type        = number
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key for the failure log; null for CloudWatch's own encryption."
  type        = string
  default     = null
}
