variable "secret_id" {
  description = "The ID of the secret"
  type        = string
}

variable "secret_value" {
  description = "The value of the secret"
  type        = string
  sensitive   = true
}

variable "service_account_email" {
  description = "Service account email to grant access to the secret"
  type        = string
  default     = ""
}

variable "labels" {
  description = "Labels to apply to the secret"
  type        = map(string)
  default     = {}
}
