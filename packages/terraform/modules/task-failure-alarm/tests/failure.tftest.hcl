# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
}

variables {
  name                     = "app-dev-jobs"
  cluster_arn              = "arn:aws:ecs:ap-southeast-2:111122223333:cluster/app-dev"
  task_definition_families = ["app-dev-job-expire-sessions"]
  alarm_topic_arn          = "arn:aws:sns:ap-southeast-2:111122223333:alarms"
  retention_days           = 30
}

run "a_failed_or_unstarted_task_raises_the_alarm" {
  command = plan

  assert {
    condition     = jsondecode(aws_cloudwatch_event_rule.failed.event_pattern).detail.group == ["family:app-dev-job-expire-sessions"]
    error_message = "Only the given families' tasks must be watched."
  }

  assert {
    condition = jsondecode(aws_cloudwatch_event_rule.failed.event_pattern).detail["$or"] == [
      { containers = { exitCode = [{ "anything-but" = 0 }] } },
      { stopCode = ["TaskFailedToStart"] },
    ]
    error_message = "A non-zero exit and a failure to start must both count as failures."
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.failed.alarm_actions == toset(["arn:aws:sns:ap-southeast-2:111122223333:alarms"])
    error_message = "The alarm must notify the alarm topic."
  }
}
