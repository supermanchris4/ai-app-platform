# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {}

variables {
  name               = "app-dev-api"
  vpc_id             = "vpc-0123456789abcdef0"
  subnet_ids         = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
  security_group_ids = ["sg-0123456789abcdef0"]
  certificate_arn    = "arn:aws:acm:ap-southeast-2:111122223333:certificate/0f0e0d0c-0b0a-0908-0706-050403020100"
  target_port        = 8000
  health_check_path  = "/api/health"
}

run "internal_and_https_only" {
  command = plan

  assert {
    condition     = aws_lb.this.internal
    error_message = "The load balancer must not be reachable from the internet."
  }

  assert {
    condition     = aws_lb.this.drop_invalid_header_fields
    error_message = "The load balancer must drop invalid headers."
  }

  assert {
    condition     = aws_lb_listener.https.protocol == "HTTPS" && aws_lb_listener.https.port == 443
    error_message = "The only listener must be HTTPS on 443."
  }

  assert {
    condition     = aws_lb_listener.https.ssl_policy == "ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09"
    error_message = "The listener must use AWS's restricted, quantum-safe TLS 1.2 and 1.3 policy."
  }

  assert {
    condition     = aws_lb_target_group.this.target_type == "ip" && aws_lb_target_group.this.health_check[0].path == "/api/health"
    error_message = "Targets must be task IPs checked on the health path."
  }
}
