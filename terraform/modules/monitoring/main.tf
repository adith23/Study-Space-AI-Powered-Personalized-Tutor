locals {
  log_groups = {
    api      = "/aws/lambda/${var.project}-${var.environment}-api"
    worker   = "/aws/lambda/${var.project}-${var.environment}-worker"
    frontend = "/aws/lambda/${var.project}-${var.environment}-frontend"
  }
}

# ── Log Groups ───────────────────────────────────────────────
# Always Free: 5 GB ingestion/month. 7-day retention to stay well within limits.

resource "aws_cloudwatch_log_group" "lambda" {
  for_each = local.log_groups

  name              = each.value
  retention_in_days = 7

  tags = { Name = each.value }
}

# ── Alarms (Always Free: 10 alarms) ─────────────────────────

# API Lambda error rate
resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "${var.project}-api-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "API Lambda errors > 5 in 10 minutes"

  dimensions = {
    FunctionName = "${var.project}-${var.environment}-api"
  }

  tags = { Name = "${var.project}-api-errors" }
}

# Worker Lambda error rate
resource "aws_cloudwatch_metric_alarm" "worker_errors" {
  alarm_name          = "${var.project}-worker-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "Worker Lambda errors > 3 in 10 minutes"

  dimensions = {
    FunctionName = "${var.project}-${var.environment}-worker"
  }

  tags = { Name = "${var.project}-worker-errors" }
}

# API Lambda p99 latency (cold start detection)
resource "aws_cloudwatch_metric_alarm" "api_duration" {
  alarm_name          = "${var.project}-api-high-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  extended_statistic  = "p99"
  threshold           = 10000 # 10 seconds
  alarm_description   = "API p99 latency > 10s (cold start issues)"

  dimensions = {
    FunctionName = "${var.project}-${var.environment}-api"
  }

  tags = { Name = "${var.project}-api-duration" }
}

# SQS Dead Letter Queue depth
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project}-dlq-not-empty"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Failed tasks sitting in dead-letter queue"

  dimensions = {
    QueueName = "${var.project}-${var.environment}-dlq"
  }

  tags = { Name = "${var.project}-dlq-alarm" }
}

# SQS queue age (tasks waiting too long)
resource "aws_cloudwatch_metric_alarm" "queue_age" {
  alarm_name          = "${var.project}-queue-old-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 1800 # 30 minutes
  alarm_description   = "Tasks queued for > 30 minutes"

  dimensions = {
    QueueName = "${var.project}-${var.environment}-tasks"
  }

  tags = { Name = "${var.project}-queue-age-alarm" }
}
