variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS task queue"
  type        = string
}

variable "log_group_arns" {
  description = "List of CloudWatch Log Group ARNs"
  type        = list(string)
}
