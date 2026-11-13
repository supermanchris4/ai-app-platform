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

variable "oidc_provider_arn" {
  description = "The account's GitHub Actions OIDC provider."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:oidc-provider/token\\.actions\\.githubusercontent\\.com$", var.oidc_provider_arn))
    error_message = "oidc_provider_arn must be the ARN of the token.actions.githubusercontent.com OIDC provider."
  }
}

variable "subjects" {
  description = "The exact OIDC subjects that may assume the role, such as repository_id:123:ref:refs/heads/main. Wildcards are not allowed."
  type        = list(string)

  validation {
    condition     = length(var.subjects) > 0 && alltrue([for subject in var.subjects : !strcontains(subject, "*") && !strcontains(subject, "?")])
    error_message = "subjects must list at least one subject, with no wildcards."
  }
}

variable "permissions_boundary_arn" {
  description = "The permissions boundary on the role."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::([0-9]{12}|aws):policy/.+$", var.permissions_boundary_arn))
    error_message = "permissions_boundary_arn must be an IAM policy ARN."
  }
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

variable "max_session_hours" {
  description = "The longest session a workflow can have with the role, in hours."
  type        = number
  default     = 1

  validation {
    condition     = var.max_session_hours >= 1 && var.max_session_hours <= 12
    error_message = "max_session_hours must be from 1 to 12."
  }
}
