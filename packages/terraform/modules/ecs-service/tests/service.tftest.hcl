# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {}

variables {
  name                = "app-dev-api"
  cluster_arn         = "arn:aws:ecs:ap-southeast-2:111122223333:cluster/app-dev"
  task_definition_arn = "arn:aws:ecs:ap-southeast-2:111122223333:task-definition/app-dev-api:1"
  desired_count       = 2
  subnet_ids          = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
  security_group_ids  = ["sg-0123456789abcdef0"]
  target_group_arn    = "arn:aws:elasticloadbalancing:ap-southeast-2:111122223333:targetgroup/app-dev-api/0123456789abcdef"
  container_name      = "api"
  container_port      = 8000
}

run "private_and_rolled_back_on_failure" {
  command = plan

  assert {
    condition     = !aws_ecs_service.this.network_configuration[0].assign_public_ip
    error_message = "Tasks must have no public IP address."
  }

  assert {
    condition     = aws_ecs_service.this.deployment_circuit_breaker[0].enable && aws_ecs_service.this.deployment_circuit_breaker[0].rollback
    error_message = "A failed deployment must be rolled back by the circuit breaker."
  }

  assert {
    condition     = !aws_ecs_service.this.enable_execute_command
    error_message = "No one may open a shell in the tasks."
  }
}
