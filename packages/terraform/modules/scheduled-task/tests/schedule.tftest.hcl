# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = { account_id = "111122223333" }
  }

  mock_data "aws_partition" {
    defaults = { partition = "aws" }
  }

  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
}

variables {
  name                     = "app-dev-job-expire-sessions"
  schedule_expression      = "cron(15 * * * ? *)"
  time_zone                = "Australia/Perth"
  cluster_arn              = "arn:aws:ecs:ap-southeast-2:111122223333:cluster/app-dev"
  task_definition_family   = "app-dev-job-expire-sessions"
  region                   = "ap-southeast-2"
  subnet_ids               = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
  security_group_ids       = ["sg-0123456789abcdef0"]
  pass_role_arns           = ["arn:aws:iam::111122223333:role/app-dev-api"]
  permissions_boundary_arn = "arn:aws:iam::111122223333:policy/app-boundary"
}

run "runs_the_latest_revision_privately" {
  command = plan

  assert {
    condition     = aws_scheduler_schedule.this.target[0].ecs_parameters[0].task_definition_arn == "arn:aws:ecs:ap-southeast-2:111122223333:task-definition/app-dev-job-expire-sessions"
    error_message = "The schedule must run the family's latest revision, which the pipeline registers."
  }

  assert {
    condition     = !aws_scheduler_schedule.this.target[0].ecs_parameters[0].network_configuration[0].assign_public_ip
    error_message = "The job's task must have no public IP address."
  }

  assert {
    condition     = aws_scheduler_schedule.this.schedule_expression_timezone == "Australia/Perth"
    error_message = "The schedule must run in the given time zone."
  }

  assert {
    condition     = aws_iam_role.scheduler.permissions_boundary == "arn:aws:iam::111122223333:policy/app-boundary"
    error_message = "The scheduler's role must carry the permissions boundary."
  }
}
