# web-acl

An AWS WAF web ACL for a CloudFront distribution (the template's 12-aws-deployment.md#edge): AWS's managed core rule set, known bad inputs and IP reputation list, and a rate limit per client IP on the API. A CloudFront web ACL lives in us-east-1, so the caller passes a provider for that region.

## Usage

```hcl
module "web_acl" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/web-acl?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The web ACL's name. |
| `rate_limit` | `number` | No | Requests per client IP in any 5 minutes to rate_limited_path_prefix before the client is blocked. |
| `rate_limited_path_prefix` | `string` | No | The path prefix the rate limit applies to. |

## Outputs

| Name | Description |
|---|---|
| `arn` | The web ACL's ARN, which the distribution names. |
