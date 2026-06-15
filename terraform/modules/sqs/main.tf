# Dead-letter queue for failed tasks
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-${var.environment}-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = { Name = "${var.project}-dlq" }
}

# Main task queue (replaces Celery + Redis as task broker)
# Always Free: 1M requests/month
resource "aws_sqs_queue" "tasks" {
  name                       = "${var.project}-${var.environment}-tasks"
  visibility_timeout_seconds = 960  # > Lambda max timeout (900s) + 60s buffer
  message_retention_seconds  = 345600  # 4 days
  receive_wait_time_seconds  = 20     # Long polling (reduces SQS API calls)

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3 # Retry 3 times before sending to DLQ
  })

  tags = { Name = "${var.project}-tasks" }
}
