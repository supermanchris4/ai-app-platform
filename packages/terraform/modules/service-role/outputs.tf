output "arn" {
  description = "The role's ARN."
  value       = aws_iam_role.this.arn
}

output "name" {
  description = "The role's name."
  value       = aws_iam_role.this.name
}
