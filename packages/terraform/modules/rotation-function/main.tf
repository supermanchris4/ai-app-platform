# AWS's Secrets Manager single-user rotation function for PostgreSQL, installed from the Serverless
# Application Repository through CloudFormation, using the bootstrap's CloudFormation role: the
# function's role cannot carry the permissions boundary. See README.md.
data "aws_serverlessapplicationrepository_application" "rotation" {
  application_id   = var.application_id
  semantic_version = var.application_version
}

locals {
  function_name = "${var.name}-rotation"
  parameters = merge(
    {
      endpoint            = "https://secretsmanager.${var.region}.amazonaws.com"
      functionName        = local.function_name
      vpcSubnetIds        = join(",", var.subnet_ids)
      vpcSecurityGroupIds = join(",", var.security_group_ids)
    },
    var.kms_key_arn == null ? {} : { kmsKeyArn = var.kms_key_arn },
  )
}

# The template's address is a signed URL that changes on every read, so it is ignored once the stack
# exists; a new application_version replaces the stack instead.
resource "terraform_data" "version" {
  input = data.aws_serverlessapplicationrepository_application.rotation.semantic_version
}

resource "aws_cloudformation_stack" "rotation" {
  name         = "${var.name}-rotation"
  template_url = data.aws_serverlessapplicationrepository_application.rotation.template_url
  parameters   = local.parameters
  # The template creates the function's role and uses the Serverless transform. The application's
  # CAPABILITY_RESOURCE_POLICY applies only to installing through the repository itself.
  capabilities = ["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"]
  iam_role_arn = var.cloudformation_role_arn

  lifecycle {
    ignore_changes       = [template_url]
    replace_triggered_by = [terraform_data.version]
  }
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
