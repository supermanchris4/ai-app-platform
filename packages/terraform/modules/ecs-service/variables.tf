variable "name" {
  description = "The service's name."
  type        = string
}

variable "cluster_arn" {
  description = "The cluster the service runs in."
  type        = string
}

variable "task_definition_arn" {
  description = "The first task definition revision. Later ones are set by the deployment pipeline, and Terraform leaves them be."
  type        = string
}

variable "desired_count" {
  description = "The number of tasks."
  type        = number
}

variable "subnet_ids" {
  description = "Private subnets for the tasks, in at least two Availability Zones."
  type        = list(string)
}

variable "security_group_ids" {
  description = "The tasks' security groups."
  type        = list(string)
}

variable "target_group_arn" {
  description = "The load balancer target group the tasks register in."
  type        = string
}

variable "container_name" {
  description = "The container the load balancer forwards to."
  type        = string
}

variable "container_port" {
  description = "The port the load balancer forwards to."
  type        = number
}
