# An internal Application Load Balancer, reachable only from inside the VPC, with one HTTPS listener
# forwarding to IP targets (Fargate tasks) (the template's 12-aws-deployment.md#compute).
# Access logs would need their own bucket; every request is already logged by the API, with its
# correlation ID, and at the edge by CloudFront and AWS WAF.
# nosemgrep: terraform.aws.security.aws-elb-access-logs-not-enabled.aws-elb-access-logs-not-enabled
resource "aws_lb" "this" {
  name                       = var.name
  internal                   = true
  load_balancer_type         = "application"
  subnets                    = var.subnet_ids
  security_groups            = var.security_group_ids
  drop_invalid_header_fields = true
  enable_deletion_protection = var.deletion_protection
}

resource "aws_lb_target_group" "this" {
  name                 = var.name
  vpc_id               = var.vpc_id
  target_type          = "ip"
  port                 = var.target_port
  protocol             = "HTTP"
  deregistration_delay = 30

  health_check {
    path                = var.health_check_path
    matcher             = "200"
    interval            = 15
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  # TLS 1.2 and 1.3 only, with forward secrecy and authenticated encryption (no CBC ciphers), and
  # quantum-safe key exchange for TLS 1.3 clients: AWS's recommended policy. Not an input, so no
  # caller can weaken it. CloudFront reaches it over TLS 1.2 with ECDHE and AES-GCM.
  ssl_policy      = "ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09"
  certificate_arn = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}
