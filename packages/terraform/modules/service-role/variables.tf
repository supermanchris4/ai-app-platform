variable "name" {
  description = "The role's name."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", var.name))
    error_message = "name must be a valid IAM role name of at most 64 characters."
  }
}

variable "description" {
  description = "What the role is for."
  type        = string
  default     = ""
}

variable "service_principals" {
  description = "The AWS services that may assume the role, such as ecs-tasks.amazonaws.com."
  type        = list(string)

  validation {
    condition     = length(var.service_principals) > 0 && alltrue([for principal in var.service_principals : endswith(principal, ".amazonaws.com")])
    error_message = "service_principals must name at least one service, such as ecs-tasks.amazonaws.com."
  }
}

variable "source_account" {
  description = "The account the services must act for, guarding against the confused deputy problem; null to not check."
  type        = string
  default     = null
}

variable "permissions_boundary_arn" {
  description = "The permissions boundary on the role."
  type        = string
}

variable "managed_policy_arns" {
  description = "Managed policies attached to the role."
  type        = list(string)
  default     = []
}

variable "inline_policies" {
  description = "Policy documents, in JSON, held on the role, by name. The names must be known at plan time; the documents need not be."
  type        = map(string)
  default     = {}
}
