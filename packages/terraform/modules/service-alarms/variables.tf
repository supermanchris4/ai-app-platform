variable "name" {
  description = "The prefix for the alarms' names."
  type        = string
}

variable "cluster_name" {
  description = "The service's ECS cluster."
  type        = string
}

variable "service_name" {
  description = "The ECS service."
  type        = string
}

variable "desired_count" {
  description = "The number of tasks the service should run."
  type        = number
}

variable "load_balancer_arn_suffix" {
  description = "The load balancer's ARN suffix, as CloudWatch names it."
  type        = string
}

variable "target_group_arn_suffix" {
  description = "The service's target group ARN suffix, as CloudWatch names it."
  type        = string
}

variable "alarm_topic_arn" {
  description = "The SNS topic the alarms notify, when they fire and when they clear."
  type        = string
}

variable "utilisation_percent" {
  description = "CPU and memory use, as a percentage, that raises an alarm after 15 minutes."
  type        = number
  default     = 80
}

variable "server_errors" {
  description = "Responses with a 5xx status from the service in 5 minutes that raise an alarm."
  type        = number
  default     = 10
}

variable "response_time_seconds" {
  description = "The p95 response time, in seconds, that raises an alarm after 15 minutes."
  type        = number
}
