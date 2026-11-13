# A permissions boundary for every role an application's pipelines create or use. It allows the
# listed services, and IAM only to manage the application's own roles, each of which must carry this
# same boundary; nothing under it can remove or change the boundary, or change the protected roles.
# The policy document is also the deploy role's own permissions (see outputs).
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

locals {
  account     = data.aws_caller_identity.current.account_id
  partition   = data.aws_partition.current.partition
  policy_arn  = "arn:${local.partition}:iam::${local.account}:policy/${var.name}"
  own_roles   = "arn:${local.partition}:iam::${local.account}:role/${var.role_name_prefix}*"
  protected   = [for name in var.protected_role_names : "arn:${local.partition}:iam::${local.account}:role/${name}"]
  service_ops = [for service in var.allowed_services : "${service}:*"]
}

# A deploy role manages whole services, including buckets (AWS-0345), and passes the application's
# own roles to ECS and EventBridge (AWS-0342); the IAM rules below confine it to those roles.
#trivy:ignore:AWS-0345
#trivy:ignore:AWS-0342
data "aws_iam_policy_document" "boundary" {
  statement {
    sid       = "AllowedServices"
    actions   = local.service_ops
    resources = ["*"]
  }

  statement {
    sid       = "ReadIam"
    actions   = ["iam:Get*", "iam:List*"]
    resources = ["*"]
  }

  statement {
    sid = "CreateOwnRolesWithThisBoundary"
    actions = [
      "iam:CreateRole",
      "iam:PutRolePermissionsBoundary",
      "iam:PutRolePolicy",
      "iam:AttachRolePolicy",
    ]
    resources = [local.own_roles]

    condition {
      test     = "StringEquals"
      variable = "iam:PermissionsBoundary"
      values   = [local.policy_arn]
    }
  }

  statement {
    sid = "ManageOwnRoles"
    actions = [
      "iam:DeleteRole",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateRole",
      "iam:UpdateRoleDescription",
      "iam:UpdateAssumeRolePolicy",
      "iam:PassRole",
    ]
    resources = [local.own_roles]
  }

  statement {
    sid       = "ServiceLinkedRoles"
    actions   = ["iam:CreateServiceLinkedRole"]
    resources = ["arn:${local.partition}:iam::${local.account}:role/aws-service-role/*"]
  }

  statement {
    sid    = "KeepTheBoundary"
    effect = "Deny"
    actions = [
      "iam:DeleteRolePermissionsBoundary",
      "iam:CreatePolicyVersion",
      "iam:DeletePolicy",
      "iam:DeletePolicyVersion",
      "iam:SetDefaultPolicyVersion",
    ]
    resources = [local.policy_arn, local.own_roles]
  }

  dynamic "statement" {
    for_each = length(local.protected) > 0 ? [1] : []

    content {
      sid    = "KeepTheProtectedRoles"
      effect = "Deny"
      actions = [
        "iam:AttachRolePolicy",
        "iam:DeleteRole",
        "iam:DeleteRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePermissionsBoundary",
        "iam:PutRolePolicy",
        "iam:UpdateAssumeRolePolicy",
        "iam:UpdateRole",
      ]
      resources = local.protected
    }
  }
}

resource "aws_iam_policy" "boundary" {
  name        = var.name
  description = "Permissions boundary for the roles of ${var.role_name_prefix}"
  policy      = data.aws_iam_policy_document.boundary.json
}
