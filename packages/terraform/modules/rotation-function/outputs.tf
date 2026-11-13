output "function_arn" {
  description = "The rotation function, which each rotated secret names."
  value       = "arn:${data.aws_partition.current.partition}:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${local.function_name}"

  depends_on = [aws_cloudformation_stack.rotation]
}

output "application_version" {
  description = "The version of AWS's application installed; pin it in application_version."
  value       = data.aws_serverlessapplicationrepository_application.rotation.semantic_version
}
