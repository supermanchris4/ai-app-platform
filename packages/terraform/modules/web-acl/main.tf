# An AWS WAF web ACL for a CloudFront distribution (the template's 12-aws-deployment.md#edge): AWS's managed
# core rule set, known bad inputs and IP reputation list, and a rate limit per client IP on the API.
# A CloudFront web ACL lives in us-east-1, so the caller passes a provider for that region.
locals {
  managed_rule_groups = {
    AWSManagedRulesAmazonIpReputationList = 1
    AWSManagedRulesCommonRuleSet          = 2
    AWSManagedRulesKnownBadInputsRuleSet  = 3
  }
}

resource "aws_wafv2_web_acl" "this" {
  name  = var.name
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  dynamic "rule" {
    for_each = local.managed_rule_groups

    content {
      name     = rule.key
      priority = rule.value

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = rule.key
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = rule.key
        sampled_requests_enabled   = true
      }
    }
  }

  rule {
    name     = "RateLimitPerClient"
    priority = 10

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"

        scope_down_statement {
          byte_match_statement {
            search_string         = var.rate_limited_path_prefix
            positional_constraint = "STARTS_WITH"

            field_to_match {
              uri_path {}
            }

            text_transformation {
              priority = 0
              type     = "NONE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitPerClient"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = var.name
    sampled_requests_enabled   = true
  }
}
