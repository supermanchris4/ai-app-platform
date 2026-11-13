# The three security groups of a web service (the template's 12-aws-deployment.md#network-and-security-groups):
#
#   load balancer  in: HTTPS from CloudFront only     out: the tasks on the container port
#   tasks          in: the container port from the LB  out: the database; HTTPS to AWS and issuers
#   database       in: its port from the tasks only    out: none
data "aws_ec2_managed_prefix_list" "load_balancer_sources" {
  name = var.load_balancer_source_prefix_list
}

resource "aws_security_group" "load_balancer" {
  name        = "${var.name}-load-balancer"
  description = "The internal load balancer: HTTPS from CloudFront only"
  vpc_id      = var.vpc_id
}

resource "aws_security_group" "tasks" {
  name        = "${var.name}-tasks"
  description = "The service's tasks: reached only from the load balancer"
  vpc_id      = var.vpc_id
}

resource "aws_security_group" "database" {
  name        = "${var.name}-database"
  description = "The database: reached only from the service's tasks"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "load_balancer_from_cloudfront" {
  security_group_id = aws_security_group.load_balancer.id
  description       = "HTTPS from CloudFront"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  prefix_list_id    = data.aws_ec2_managed_prefix_list.load_balancer_sources.id
}

resource "aws_vpc_security_group_egress_rule" "load_balancer_to_tasks" {
  security_group_id            = aws_security_group.load_balancer.id
  description                  = "To the tasks"
  ip_protocol                  = "tcp"
  from_port                    = var.container_port
  to_port                      = var.container_port
  referenced_security_group_id = aws_security_group.tasks.id
}

resource "aws_vpc_security_group_ingress_rule" "tasks_from_load_balancer" {
  security_group_id            = aws_security_group.tasks.id
  description                  = "From the load balancer"
  ip_protocol                  = "tcp"
  from_port                    = var.container_port
  to_port                      = var.container_port
  referenced_security_group_id = aws_security_group.load_balancer.id
}

resource "aws_vpc_security_group_egress_rule" "tasks_to_database" {
  security_group_id            = aws_security_group.tasks.id
  description                  = "To the database"
  ip_protocol                  = "tcp"
  from_port                    = var.database_port
  to_port                      = var.database_port
  referenced_security_group_id = aws_security_group.database.id
}

# AWS service endpoints and the identity providers' sign-in endpoints have no fixed addresses, so
# HTTPS out is open (AWS-0104); nothing can reach the tasks from outside but the load balancer.
#trivy:ignore:AWS-0104
resource "aws_vpc_security_group_egress_rule" "tasks_https_out" {
  security_group_id = aws_security_group.tasks.id
  description       = "HTTPS to AWS services and the identity providers"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "database_from_tasks" {
  security_group_id            = aws_security_group.database.id
  description                  = "From the service's tasks"
  ip_protocol                  = "tcp"
  from_port                    = var.database_port
  to_port                      = var.database_port
  referenced_security_group_id = aws_security_group.tasks.id
}
