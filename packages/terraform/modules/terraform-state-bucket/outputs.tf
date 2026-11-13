output "name" {
  description = "The bucket's name, given to terraform init as the backend's bucket."
  value       = aws_s3_bucket.state.id
}

output "arn" {
  description = "The bucket's ARN."
  value       = aws_s3_bucket.state.arn
}
