variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "api_image_uri" {
  description = "ECR image URI for the API Lambda"
  type        = string
}

variable "worker_image_uri" {
  description = "ECR image URI for the Worker Lambda"
  type        = string
}

variable "frontend_image_uri" {
  description = "ECR image URI for the Frontend Lambda"
  type        = string
}

variable "api_execution_role" {
  description = "IAM role ARN for the API Lambda"
  type        = string
}

variable "worker_execution_role" {
  description = "IAM role ARN for the Worker Lambda"
  type        = string
}

variable "frontend_execution_role" {
  description = "IAM role ARN for the Frontend Lambda"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS task queue for worker trigger"
  type        = string
}
