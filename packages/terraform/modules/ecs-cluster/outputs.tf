output "name" {
  description = "The cluster's name."
  value       = aws_ecs_cluster.this.name
}

output "arn" {
  description = "The cluster's ARN."
  value       = aws_ecs_cluster.this.arn
}
