# A CloudWatch log group with a retention period. A customer-managed key is optional (AWS-0017);
# without one, CloudWatch encrypts logs with its own key.
#trivy:ignore:AWS-0017
resource "aws_cloudwatch_log_group" "this" {
  name              = var.name
  retention_in_days = var.retention_days
  kms_key_id        = var.kms_key_arn
}
