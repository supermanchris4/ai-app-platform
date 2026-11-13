output "arn" {
  description = "The role's ARN, which a workflow names to assume it."
  value       = aws_iam_role.this.arn
}

output "name" {
  description = "The role's name."
  value       = aws_iam_role.this.name
}
