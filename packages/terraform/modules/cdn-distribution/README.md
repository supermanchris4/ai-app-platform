# cdn-distribution

One CloudFront distribution, the application's only entry point (the template's 12-aws-deployment.md#edge): the web build from a private bucket through Origin Access Control, and the API through a VPC origin to the internal load balancer over HTTPS, behind AWS WAF and with strict response headers.

## Usage

```hcl
module "cdn_distribution" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/cdn-distribution?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

Its tests, in `tests/`, run with `terraform test` against mocked providers.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The prefix for the distribution's resource names. |
| `web_bucket_arn` | `string` | Yes | The private bucket holding the web build. |
| `web_bucket_regional_domain_name` | `string` | Yes | The web bucket's regional domain name. |
| `load_balancer_arn` | `string` | Yes | The internal load balancer the API is reached through, by a VPC origin. |
| `api_origin_domain_name` | `string` | Yes | The name the load balancer's certificate is for; CloudFront connects to the API with it. |
| `api_path_pattern` | `string` | No | The paths sent to the API; everything else is the web build. |
| `aliases` | `list(string)` | No | Custom domain names for the distribution; empty for CloudFront's own domain. |
| `certificate_arn` | `string` | No | The ACM certificate in us-east-1 for the aliases; null when there are none. |
| `minimum_tls_policy` | `string` | No | The viewer security policy when certificate_arn is set: TLSv1.2_2021 allows TLS 1.2 and 1.3, TLSv1.2_2025 narrows TLS 1.2's ciphers, and TLSv1.3_2025 allows TLS 1.3 only, which refuses callers limited to TLS 1.2. Without a certificate, CloudFront's own certificate sets the policy. |
| `web_acl_arn` | `string` | Yes | The AWS WAF web ACL in front of the distribution. |
| `content_security_policy` | `string` | No | The Content Security Policy header for every response. |
| `price_class` | `string` | No | Which edge locations serve the distribution. |

## Outputs

| Name | Description |
|---|---|
| `id` | The distribution's ID, which the pipeline invalidates after uploading a web build. |
| `domain_name` | CloudFront's own domain name for the distribution. |
| `web_bucket_read_policy` | The bucket policy statement letting this distribution read the web bucket. |
