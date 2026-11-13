# A Secrets Manager secret created without a value: whatever sets the value (a task, an operator
# or a rotation) does so outside Terraform, so no secret value is in code or state (Standard D-13).
# A customer-managed key is optional (AWS-0098); without one, the AWS-managed key is used.
#trivy:ignore:AWS-0098
resource "aws_secretsmanager_secret" "this" {
  name                    = var.name
  description             = var.description
  kms_key_id              = var.kms_key_arn
  recovery_window_in_days = var.recovery_window_days
}

# Rotation starts at the first scheduled time, not now: the secret has no value until it is set.
resource "aws_secretsmanager_secret_rotation" "this" {
  count = var.rotate ? 1 : 0

  secret_id           = aws_secretsmanager_secret.this.id
  rotation_lambda_arn = var.rotation_function_arn
  rotate_immediately  = false

  rotation_rules {
    automatically_after_days = var.rotation_days
  }
}
