output "arn" {
  description = "The revision's ARN."
  value       = aws_ecs_task_definition.this.arn
}

output "family" {
  description = "The task definition's family, which the pipeline registers new revisions in."
  value       = aws_ecs_task_definition.this.family
}

output "container_name" {
  description = "The container's name."
  value       = var.container_name
}
