# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {}

variables {
  name                     = "app-dev-api"
  cluster_name             = "app-dev"
  service_name             = "app-dev-api"
  desired_count            = 2
  load_balancer_arn_suffix = "app/app-dev-api/0123456789abcdef"
  target_group_arn_suffix  = "targetgroup/app-dev-api/0123456789abcdef"
  alarm_topic_arn          = "arn:aws:sns:ap-southeast-2:111122223333:alarms"
  response_time_seconds    = 0.5
}

run "every_alarm_notifies_the_topic" {
  command = plan

  assert {
    condition = alltrue([
      for alarm in [
        aws_cloudwatch_metric_alarm.running_tasks,
        aws_cloudwatch_metric_alarm.cpu,
        aws_cloudwatch_metric_alarm.memory,
        aws_cloudwatch_metric_alarm.server_errors,
        aws_cloudwatch_metric_alarm.response_time,
      ] : alarm.alarm_actions == toset([var.alarm_topic_arn]) && alarm.ok_actions == toset([var.alarm_topic_arn])
    ])
    error_message = "Every alarm must notify the topic when it fires and when it clears."
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.running_tasks.threshold == 2 && aws_cloudwatch_metric_alarm.running_tasks.comparison_operator == "LessThanThreshold"
    error_message = "Fewer running tasks than wanted must raise the alarm."
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.running_tasks.treat_missing_data == "breaching"
    error_message = "No running-task data at all, as when every task has stopped, must raise the alarm."
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.response_time.extended_statistic == "p95" && aws_cloudwatch_metric_alarm.response_time.threshold == 0.5
    error_message = "The response-time alarm must watch p95 against the target."
  }
}
