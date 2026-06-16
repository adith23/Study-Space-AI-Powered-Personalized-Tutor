variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "api_function_url" {
  description = "The Lambda Function URL for the API"
  type        = string
}

variable "frontend_function_url" {
  description = "The Lambda Function URL for the Frontend"
  type        = string
}

variable "api_function_name" {
  description = "The Lambda Function Name for the API"
  type        = string
}

variable "frontend_function_name" {
  description = "The Lambda Function Name for the Frontend"
  type        = string
}
