variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "api_function_url" {
  description = "API Lambda Function URL (origin)"
  type        = string
}

variable "frontend_function_url" {
  description = "Frontend Lambda Function URL (origin)"
  type        = string
}
