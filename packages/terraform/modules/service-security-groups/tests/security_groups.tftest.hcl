# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {
  mock_data "aws_ec2_managed_prefix_list" {
    defaults = { id = "pl-0123456789abcdef0" }
  }
}

variables {
  name           = "app-dev"
  vpc_id         = "vpc-0123456789abcdef0"
  container_port = 8000
}

run "each_group_reached_only_from_the_one_before" {
  command = plan

  assert {
    condition     = aws_vpc_security_group_ingress_rule.load_balancer_from_cloudfront.prefix_list_id == "pl-0123456789abcdef0" && aws_vpc_security_group_ingress_rule.load_balancer_from_cloudfront.from_port == 443
    error_message = "The load balancer must accept only HTTPS from CloudFront's prefix list."
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.load_balancer_from_cloudfront.cidr_ipv4 == null
    error_message = "The load balancer must not accept any address range."
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.tasks_from_load_balancer.from_port == 8000 && aws_vpc_security_group_ingress_rule.tasks_from_load_balancer.cidr_ipv4 == null
    error_message = "The tasks must accept only the container port, from the load balancer's group."
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.database_from_tasks.from_port == 5432 && aws_vpc_security_group_ingress_rule.database_from_tasks.cidr_ipv4 == null
    error_message = "The database must accept only its port, from the tasks' group."
  }
}
