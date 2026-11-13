variable "name" {
  description = "The boundary policy's name."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{1,128}$", var.name))
    error_message = "name must be a valid IAM policy name."
  }
}

variable "allowed_services" {
  description = "The AWS service prefixes roles under the boundary may use, such as ecs or s3."
  type        = list(string)

  validation {
    condition     = length(var.allowed_services) > 0 && alltrue([for service in var.allowed_services : can(regex("^[a-z0-9-]+$", service)) && service != "iam"])
    error_message = "allowed_services must list service prefixes; IAM is granted only as this module allows it."
  }
}

variable "role_name_prefix" {
  description = "Roles may create, change, pass and delete only roles whose names start with this, and only with this boundary."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{2,40}$", var.role_name_prefix))
    error_message = "role_name_prefix must be 2 to 40 characters valid in a role name."
  }
}

variable "protected_role_names" {
  description = "Roles no role under the boundary may change, such as the pipeline roles themselves."
  type        = list(string)
  default     = []
}
