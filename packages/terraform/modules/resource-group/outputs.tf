output "name" {
  description = "The Resource Group's name."
  value       = aws_resourcegroups_group.this.name
}

output "arn" {
  description = "The Resource Group's ARN."
  value       = aws_resourcegroups_group.this.arn
}
