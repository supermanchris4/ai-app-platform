output "name" {
  description = "The log group's name."
  value       = aws_cloudwatch_log_group.this.name
}

output "arn" {
  description = "The log group's ARN."
  value       = aws_cloudwatch_log_group.this.arn
}
