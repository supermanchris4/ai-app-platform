output "id" {
  description = "The distribution's ID, which the pipeline invalidates after uploading a web build."
  value       = aws_cloudfront_distribution.this.id
}

output "domain_name" {
  description = "CloudFront's own domain name for the distribution."
  value       = aws_cloudfront_distribution.this.domain_name
}

output "web_bucket_read_policy" {
  description = "The bucket policy statement letting this distribution read the web bucket."
  value       = data.aws_iam_policy_document.web_bucket_read.json
}
