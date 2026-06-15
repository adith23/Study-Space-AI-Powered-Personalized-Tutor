variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g. production, staging)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "study-space"
}

variable "api_image_uri" {
  description = "ECR Public image URI for the backend API Lambda"
  type        = string
}

variable "worker_image_uri" {
  description = "ECR Public image URI for the worker Lambda"
  type        = string
}

variable "frontend_image_uri" {
  description = "ECR Public image URI for the frontend Lambda"
  type        = string
}
