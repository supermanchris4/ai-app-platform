output "arn" {
  description = "The secret's ARN."
  value       = aws_secretsmanager_secret.this.arn
}

output "name" {
  description = "The secret's name."
  value       = aws_secretsmanager_secret.this.name
}
