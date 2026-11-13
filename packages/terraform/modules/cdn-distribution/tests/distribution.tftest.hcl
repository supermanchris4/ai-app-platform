# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {
  mock_data "aws_cloudfront_origin_request_policy" {
    defaults = { id = "b689b0a8-53d0-40ab-baf2-68738e2966ac" }
  }

  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
}

variables {
  name                            = "app-dev"
  web_bucket_arn                  = "arn:aws:s3:::app-dev-web-111122223333"
  web_bucket_regional_domain_name = "app-dev-web-111122223333.s3.ap-southeast-2.amazonaws.com"
  load_balancer_arn               = "arn:aws:elasticloadbalancing:ap-southeast-2:111122223333:loadbalancer/app/app-dev-api/0123456789abcdef"
  api_origin_domain_name          = "api.example.com"
  web_acl_arn                     = "arn:aws:wafv2:us-east-1:111122223333:global/webacl/app-dev/0f0e0d0c"
}

run "api_uncached_and_https_only" {
  command = plan

  assert {
    condition     = one([for behaviour in aws_cloudfront_distribution.this.ordered_cache_behavior : behaviour.viewer_protocol_policy if behaviour.path_pattern == "/api/*"]) == "https-only"
    error_message = "The API must be reached over HTTPS only."
  }

  assert {
    condition     = aws_cloudfront_cache_policy.api.max_ttl <= 1 && aws_cloudfront_cache_policy.api.default_ttl == 0
    error_message = "API responses must not be cached."
  }

  assert {
    condition     = aws_cloudfront_vpc_origin.api.vpc_origin_endpoint_config[0].origin_protocol_policy == "https-only"
    error_message = "CloudFront must reach the load balancer over HTTPS."
  }
}

run "pages_routed_and_assets_cached" {
  command = plan

  assert {
    condition     = length(aws_cloudfront_distribution.this.default_cache_behavior[0].function_association) == 1
    error_message = "Single-page routing must run on the web interface's pages."
  }

  assert {
    condition     = alltrue([for behaviour in aws_cloudfront_distribution.this.ordered_cache_behavior : length(behaviour.function_association) == 0])
    error_message = "Single-page routing must not run on the API or the assets, so an API error is never replaced."
  }

  assert {
    condition     = aws_cloudfront_cache_policy.assets.min_ttl == 31536000 && aws_cloudfront_cache_policy.pages.default_ttl == 0
    error_message = "Hashed assets must be cached for a year, and pages revalidated."
  }
}

run "strict_response_headers" {
  command = plan

  assert {
    condition     = strcontains(aws_cloudfront_response_headers_policy.security.security_headers_config[0].content_security_policy[0].content_security_policy, "script-src 'self'")
    error_message = "Scripts must come only from the application's own origin."
  }

  assert {
    condition     = aws_cloudfront_response_headers_policy.security.security_headers_config[0].frame_options[0].frame_option == "DENY"
    error_message = "The application must not be framed."
  }
}

run "viewers_need_tls_1_2_or_later_with_a_certificate" {
  command = plan

  variables {
    aliases         = ["app.example.com"]
    certificate_arn = "arn:aws:acm:us-east-1:111122223333:certificate/0f0e0d0c-0b0a-0908-0706-050403020100"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.viewer_certificate[0].minimum_protocol_version == "TLSv1.2_2021"
    error_message = "With a certificate, viewers must use TLS 1.2 or later by default."
  }
}

run "an_application_can_require_tls_1_3" {
  command = plan

  variables {
    aliases            = ["app.example.com"]
    certificate_arn    = "arn:aws:acm:us-east-1:111122223333:certificate/0f0e0d0c-0b0a-0908-0706-050403020100"
    minimum_tls_policy = "TLSv1.3_2025"
  }

  assert {
    condition     = aws_cloudfront_distribution.this.viewer_certificate[0].minimum_protocol_version == "TLSv1.3_2025"
    error_message = "The chosen policy must be the distribution's."
  }
}

run "an_older_policy_is_refused" {
  command = plan

  variables {
    minimum_tls_policy = "TLSv1.1_2016"
  }

  expect_failures = [var.minimum_tls_policy]
}
