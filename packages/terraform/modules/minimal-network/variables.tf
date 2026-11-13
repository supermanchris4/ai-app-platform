variable "name" {
  description = "The prefix for the network's resource names."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9-]{1,40}$", var.name))
    error_message = "name must be 1 to 40 letters, digits or hyphens."
  }
}

variable "cidr_block" {
  description = "The VPC's address range. A /16 to /24; the subnets are carved from it."
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.cidr_block, 0)) && tonumber(split("/", var.cidr_block)[1]) >= 16 && tonumber(split("/", var.cidr_block)[1]) <= 24
    error_message = "cidr_block must be an IPv4 range from /16 to /24."
  }
}

variable "availability_zones" {
  description = "The two Availability Zones for the private subnets."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) == 2 && length(distinct(var.availability_zones)) == 2
    error_message = "availability_zones must name two different zones."
  }
}

variable "flow_log_retention_days" {
  description = "Days CloudWatch keeps the VPC's flow logs."
  type        = number
  default     = 30
}

variable "kms_key_arn" {
  description = "A customer-managed KMS key for the flow logs; null for CloudWatch's own encryption."
  type        = string
  default     = null
}

variable "permissions_boundary_arn" {
  description = "The permissions boundary on the role that writes flow logs."
  type        = string
}
