# The alarms for a web service on ECS behind a load balancer (the template's 12-aws-deployment.md#monitoring),
# from AWS's recommended set: fewer running tasks than wanted, sustained CPU or memory use, server
# errors and slow responses. Each notifies the topic when it fires and when it clears.
locals {
  actions = [var.alarm_topic_arn]
  service = { ClusterName = var.cluster_name, ServiceName = var.service_name }
}

resource "aws_cloudwatch_metric_alarm" "running_tasks" {
  alarm_name          = "${var.name}-running-tasks"
  alarm_description   = "Fewer than ${var.desired_count} tasks of ${var.service_name} are running"
  namespace           = "ECS/ContainerInsights"
  metric_name         = "RunningTaskCount"
  dimensions          = local.service
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = var.desired_count
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = local.actions
  ok_actions          = local.actions
}

resource "aws_cloudwatch_metric_alarm" "cpu" {
  alarm_name          = "${var.name}-cpu"
  alarm_description   = "${var.service_name} has used over ${var.utilisation_percent}% CPU for 15 minutes"
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  dimensions          = local.service
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = var.utilisation_percent
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "missing"
  alarm_actions       = local.actions
  ok_actions          = local.actions
}

resource "aws_cloudwatch_metric_alarm" "memory" {
  alarm_name          = "${var.name}-memory"
  alarm_description   = "${var.service_name} has used over ${var.utilisation_percent}% memory for 15 minutes"
  namespace           = "AWS/ECS"
  metric_name         = "MemoryUtilization"
  dimensions          = local.service
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = var.utilisation_percent
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "missing"
  alarm_actions       = local.actions
  ok_actions          = local.actions
}

resource "aws_cloudwatch_metric_alarm" "server_errors" {
  alarm_name          = "${var.name}-server-errors"
  alarm_description   = "${var.service_name} returned over ${var.server_errors} 5xx responses in 5 minutes"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  dimensions          = { LoadBalancer = var.load_balancer_arn_suffix, TargetGroup = var.target_group_arn_suffix }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = var.server_errors
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.actions
  ok_actions          = local.actions
}

resource "aws_cloudwatch_metric_alarm" "response_time" {
  alarm_name          = "${var.name}-response-time"
  alarm_description   = "${var.service_name}'s p95 response time has been over ${var.response_time_seconds} seconds for 15 minutes"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  dimensions          = { LoadBalancer = var.load_balancer_arn_suffix, TargetGroup = var.target_group_arn_suffix }
  extended_statistic  = "p95"
  period              = 300
  evaluation_periods  = 3
  threshold           = var.response_time_seconds
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.actions
  ok_actions          = local.actions
}
