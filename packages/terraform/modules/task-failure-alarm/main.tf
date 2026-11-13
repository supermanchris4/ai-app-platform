# An alarm when a task of the given families fails: it stops with a non-zero exit code, or fails to
# start (Standard D-12). EventBridge writes each failure to a log group, which keeps a record of it,
# and a metric filter counts them for a CloudWatch alarm on the alarm topic.
locals {
  log_group_name = "/aws/events/${var.name}-task-failures"
}

# A customer-managed key is optional (AWS-0017).
#trivy:ignore:AWS-0017
resource "aws_cloudwatch_log_group" "failures" {
  name              = local.log_group_name
  retention_in_days = var.retention_days
  kms_key_id        = var.kms_key_arn
}

resource "aws_cloudwatch_event_rule" "failed" {
  name        = "${var.name}-task-failed"
  description = "A task of ${join(", ", var.task_definition_families)} failed"
  event_pattern = jsonencode({
    source        = ["aws.ecs"]
    "detail-type" = ["ECS Task State Change"]
    detail = {
      clusterArn = [var.cluster_arn]
      lastStatus = ["STOPPED"]
      group      = [for family in var.task_definition_families : "family:${family}"]
      "$or" = [
        { containers = { exitCode = [{ "anything-but" = 0 }] } },
        { stopCode = ["TaskFailedToStart"] },
      ]
    }
  })
}

data "aws_iam_policy_document" "events_write_logs" {
  statement {
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.failures.arn}:*"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com", "delivery.logs.amazonaws.com"]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "events" {
  policy_name     = "${var.name}-task-failures"
  policy_document = data.aws_iam_policy_document.events_write_logs.json
}

resource "aws_cloudwatch_event_target" "log" {
  rule = aws_cloudwatch_event_rule.failed.name
  arn  = aws_cloudwatch_log_group.failures.arn
}

resource "aws_cloudwatch_log_metric_filter" "failures" {
  name           = "${var.name}-task-failures"
  log_group_name = aws_cloudwatch_log_group.failures.name
  pattern        = ""

  metric_transformation {
    name          = "TaskFailures"
    namespace     = var.name
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_metric_alarm" "failed" {
  alarm_name          = "${var.name}-task-failed"
  alarm_description   = "A task of ${join(", ", var.task_definition_families)} failed; its stop event is in ${local.log_group_name}"
  namespace           = var.name
  metric_name         = "TaskFailures"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alarm_topic_arn]

  depends_on = [aws_cloudwatch_log_metric_filter.failures]
}
