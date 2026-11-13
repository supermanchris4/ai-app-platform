# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {}

variables {
  family             = "app-dev-api"
  container_name     = "api"
  image              = "111122223333.dkr.ecr.ap-southeast-2.amazonaws.com/app-dev-api:initial"
  cpu                = 256
  memory             = 512
  container_port     = 8000
  environment        = { APP_ENVIRONMENT = "dev" }
  secrets            = { DATABASE_CREDENTIALS = "arn:aws:secretsmanager:ap-southeast-2:111122223333:secret:app-dev-runtime" }
  execution_role_arn = "arn:aws:iam::111122223333:role/app-dev-ecs-execution"
  task_role_arn      = "arn:aws:iam::111122223333:role/app-dev-api"
  log_group_name     = "/ecs/app-dev/api"
  region             = "ap-southeast-2"
}

run "one_fargate_container" {
  command = plan

  assert {
    condition     = aws_ecs_task_definition.this.network_mode == "awsvpc" && contains(aws_ecs_task_definition.this.requires_compatibilities, "FARGATE")
    error_message = "The task must run on Fargate."
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].environment == [{ name = "APP_ENVIRONMENT", value = "dev" }]
    error_message = "Settings must be passed as the container's environment."
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].secrets[0].valueFrom == "arn:aws:secretsmanager:ap-southeast-2:111122223333:secret:app-dev-runtime"
    error_message = "Secrets must be passed by ARN, never by value."
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].logConfiguration.logDriver == "awslogs"
    error_message = "The container must log to CloudWatch."
  }
}
