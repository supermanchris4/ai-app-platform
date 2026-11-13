output "arn" {
  description = "The web ACL's ARN, which the distribution names."
  value       = aws_wafv2_web_acl.this.arn
}
