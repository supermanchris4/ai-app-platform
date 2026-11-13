variable "name" {
  description = "The web ACL's name."
  type        = string
}

variable "rate_limit" {
  description = "Requests per client IP in any 5 minutes to rate_limited_path_prefix before the client is blocked."
  type        = number
  default     = 2000

  validation {
    condition     = var.rate_limit >= 10
    error_message = "rate_limit must be at least 10."
  }
}

variable "rate_limited_path_prefix" {
  description = "The path prefix the rate limit applies to."
  type        = string
  default     = "/api/"
}
