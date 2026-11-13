output "name" {
  description = "The bucket's name."
  value       = aws_s3_bucket.this.id
}

output "regional_domain_name" {
  description = "The bucket's regional domain name, which a CloudFront origin names."
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "arn" {
  description = "The bucket's ARN."
  value       = aws_s3_bucket.this.arn
}
