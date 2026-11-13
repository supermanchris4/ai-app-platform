variable "name" {
  description = "The load balancer's name, also used for its target group. At most 28 characters."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9-]{1,28}$", var.name))
    error_message = "name must be 1 to 28 letters, digits or hyphens."
  }
}

variable "vpc_id" {
  description = "The VPC for the target group."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnets in at least two Availability Zones."
  type        = list(string)
}

variable "security_group_ids" {
  description = "The load balancer's security groups."
  type        = list(string)
}

variable "certificate_arn" {
  description = "The ACM certificate for the HTTPS listener."
  type        = string
}

variable "target_port" {
  description = "The port the targets listen on."
  type        = number
}

variable "health_check_path" {
  description = "The path the load balancer checks targets on."
  type        = string
}

variable "deletion_protection" {
  description = "Whether the load balancer is protected from deletion."
  type        = bool
  default     = false
}
