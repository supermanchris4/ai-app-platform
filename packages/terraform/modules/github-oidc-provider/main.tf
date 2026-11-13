# The account's GitHub Actions OIDC provider, which lets workflows assume roles with short-lived
# tokens instead of stored keys. An account can hold only one, so the caller creates it only where
# none exists (the template's 12-aws-deployment.md#account-bootstrap).
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}
