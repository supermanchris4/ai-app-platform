variable "name" {
  description = "The Resource Group's name."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9._-]{1,128}$", var.name))
    error_message = "name must be 1 to 128 letters, digits, dots, underscores or hyphens."
  }
}

variable "description" {
  description = "What the group holds."
  type        = string
  default     = ""
}

variable "tag_filters" {
  description = "The tags, by key and value, that a resource must all carry to be in the group."
  type        = map(string)

  validation {
    condition     = length(var.tag_filters) > 0
    error_message = "tag_filters must name at least one tag."
  }
}
