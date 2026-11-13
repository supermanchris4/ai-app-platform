output "arn" {
  description = "The OIDC provider's ARN, which roles trusted by GitHub Actions name as their federated principal."
  value       = aws_iam_openid_connect_provider.github.arn
}
