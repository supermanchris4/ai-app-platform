output "arn" {
  description = "The boundary policy's ARN, set as permissions_boundary_arn on every role."
  value       = aws_iam_policy.boundary.arn
}

output "document" {
  description = "The boundary's policy document, in JSON: the most a role under it can do, and so the deploy role's own permissions."
  value       = data.aws_iam_policy_document.boundary.json
}
