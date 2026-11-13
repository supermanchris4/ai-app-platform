variable "name" {
  description = "The schedule's name, also used for its role."
  type        = string
}

variable "schedule_expression" {
  description = "When the job runs: a cron() or rate() expression."
  type        = string

  validation {
    condition     = can(regex("^(cron|rate)\\(.+\\)$", var.schedule_expression))
    error_message = "schedule_expression must be a cron() or rate() expression."
  }
}

variable "time_zone" {
  description = "The IANA time zone the cron expression is in."
  type        = string
}

variable "cluster_arn" {
  description = "The cluster the job's task runs in."
  type        = string
}

variable "task_definition_family" {
  description = "The job's task definition family; each run uses its latest revision, which the pipeline registers."
  type        = string
}

variable "region" {
  description = "The region the task definition is in."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnets for the job's task."
  type        = list(string)
}

variable "security_group_ids" {
  description = "The job's task security groups."
  type        = list(string)
}

variable "pass_role_arns" {
  description = "The task's execution and task roles, which the scheduler passes to ECS."
  type        = list(string)
}

variable "permissions_boundary_arn" {
  description = "The permissions boundary on the scheduler's role."
  type        = string
}
