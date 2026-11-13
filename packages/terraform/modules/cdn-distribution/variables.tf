variable "name" {
  description = "The prefix for the distribution's resource names."
  type        = string
}

variable "web_bucket_arn" {
  description = "The private bucket holding the web build."
  type        = string
}

variable "web_bucket_regional_domain_name" {
  description = "The web bucket's regional domain name."
  type        = string
}

variable "load_balancer_arn" {
  description = "The internal load balancer the API is reached through, by a VPC origin."
  type        = string
}

variable "api_origin_domain_name" {
  description = "The name the load balancer's certificate is for; CloudFront connects to the API with it."
  type        = string
}

variable "api_path_pattern" {
  description = "The paths sent to the API; everything else is the web build."
  type        = string
  default     = "/api/*"
}

variable "aliases" {
  description = "Custom domain names for the distribution; empty for CloudFront's own domain."
  type        = list(string)
  default     = []
}

variable "certificate_arn" {
  description = "The ACM certificate in us-east-1 for the aliases; null when there are none."
  type        = string
  default     = null

  validation {
    condition     = var.certificate_arn == null || can(regex("^arn:aws:acm:us-east-1:", var.certificate_arn))
    error_message = "certificate_arn must be an ACM certificate in us-east-1, or null."
  }
}

variable "minimum_tls_policy" {
  description = "The viewer security policy when certificate_arn is set: TLSv1.2_2021 allows TLS 1.2 and 1.3, TLSv1.2_2025 narrows TLS 1.2's ciphers, and TLSv1.3_2025 allows TLS 1.3 only, which refuses callers limited to TLS 1.2. Without a certificate, CloudFront's own certificate sets the policy."
  type        = string
  default     = "TLSv1.2_2021"

  validation {
    condition     = contains(["TLSv1.2_2021", "TLSv1.2_2025", "TLSv1.3_2025"], var.minimum_tls_policy)
    error_message = "minimum_tls_policy must be TLSv1.2_2021, TLSv1.2_2025 or TLSv1.3_2025."
  }
}

variable "web_acl_arn" {
  description = "The AWS WAF web ACL in front of the distribution."
  type        = string
}

variable "content_security_policy" {
  description = "The Content Security Policy header for every response."
  type        = string
  default     = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
}

variable "price_class" {
  description = "Which edge locations serve the distribution."
  type        = string
  default     = "PriceClass_All"
}
