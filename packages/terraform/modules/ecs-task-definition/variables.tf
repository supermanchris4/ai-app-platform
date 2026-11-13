variable "family" {
  description = "The task definition's family."
  type        = string
}

variable "container_name" {
  description = "The container's name."
  type        = string
  default     = "app"
}

variable "image" {
  description = "The image the first revision runs. Later revisions are registered by the deployment pipeline with each build's digest."
  type        = string
}

variable "cpu" {
  description = "CPU units for the task."
  type        = number
}

variable "memory" {
  description = "Memory in MiB for the task."
  type        = number
}

variable "command" {
  description = "The command to run instead of the image's default; null for the default."
  type        = list(string)
  default     = null
}

variable "container_port" {
  description = "The port the container listens on; null for a task that serves nothing."
  type        = number
  default     = null
}

variable "health_check_command" {
  description = "The container health check's command, run in the container; null for none."
  type        = list(string)
  default     = null
}

variable "environment" {
  description = "Settings given to the container, by name. None may be secret."
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Settings read from Secrets Manager at start-up, by name: each value is a secret's ARN, optionally with a JSON key (arn:...:key::)."
  type        = map(string)
  default     = {}
}

variable "execution_role_arn" {
  description = "The role ECS uses to pull the image, write logs and read the secrets."
  type        = string
}

variable "task_role_arn" {
  description = "The role the application runs as."
  type        = string
}

variable "log_group_name" {
  description = "The CloudWatch log group the container writes to."
  type        = string
}

variable "region" {
  description = "The log group's region."
  type        = string
}
