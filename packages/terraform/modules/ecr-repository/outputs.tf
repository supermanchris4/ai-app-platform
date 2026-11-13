output "url" {
  description = "The repository's URL, to tag and push images to."
  value       = aws_ecr_repository.this.repository_url
}

output "arn" {
  description = "The repository's ARN."
  value       = aws_ecr_repository.this.arn
}

output "name" {
  description = "The repository's name."
  value       = aws_ecr_repository.this.name
}
