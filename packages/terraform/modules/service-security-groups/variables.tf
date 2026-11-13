variable "name" {
  description = "The prefix for the security groups' names."
  type        = string
}

variable "vpc_id" {
  description = "The VPC the groups belong to."
  type        = string
}

variable "container_port" {
  description = "The port the service's tasks listen on."
  type        = number
}

variable "database_port" {
  description = "The database's port."
  type        = number
  default     = 5432
}

variable "load_balancer_source_prefix_list" {
  description = "The managed prefix list allowed to reach the load balancer on HTTPS; by default CloudFront's origin-facing addresses."
  type        = string
  default     = "com.amazonaws.global.cloudfront.origin-facing"
}
