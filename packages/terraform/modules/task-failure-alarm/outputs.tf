output "alarm_name" {
  description = "The alarm raised when a task fails."
  value       = aws_cloudwatch_metric_alarm.failed.alarm_name
}

output "metric_namespace" {
  description = "The namespace of the TaskFailures metric, for dashboards."
  value       = var.name
}
