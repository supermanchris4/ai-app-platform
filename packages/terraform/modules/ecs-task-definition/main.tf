# A Fargate task definition with one container, logging to CloudWatch. The deployment pipeline
# registers later revisions with each build's image digest and the application's settings, so the
# revision Terraform creates is only the first (the template's 12-aws-deployment.md#compute).
locals {
  container = merge(
    {
      name                   = var.container_name
      image                  = var.image
      essential              = true
      readonlyRootFilesystem = false
      environment            = [for name, value in var.environment : { name = name, value = value }]
      secrets                = [for name, arn in var.secrets : { name = name, valueFrom = arn }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = var.log_group_name
          awslogs-region        = var.region
          awslogs-stream-prefix = var.container_name
        }
      }
    },
    var.command == null ? {} : { command = var.command },
    var.container_port == null ? {} : {
      portMappings = [{ containerPort = var.container_port, protocol = "tcp" }]
    },
    var.health_check_command == null ? {} : {
      healthCheck = {
        command     = var.health_check_command
        interval    = 15
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    },
  )
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.family
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn
  container_definitions    = jsonencode([local.container])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}
