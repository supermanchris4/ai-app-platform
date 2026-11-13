output "load_balancer_id" {
  description = "The load balancer's security group."
  value       = aws_security_group.load_balancer.id
}

output "tasks_id" {
  description = "The security group for the service's tasks, including one-off and scheduled tasks."
  value       = aws_security_group.tasks.id
}

output "database_id" {
  description = "The database's security group."
  value       = aws_security_group.database.id
}
