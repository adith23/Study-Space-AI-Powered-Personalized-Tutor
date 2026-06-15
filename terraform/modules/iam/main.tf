# ── Lambda Assume Role Policy ─────────────────────────────────
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ── API Lambda Role ──────────────────────────────────────────
resource "aws_iam_role" "api_lambda" {
  name               = "${var.project}-${var.environment}-api-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = { Name = "${var.project}-api-lambda" }
}

resource "aws_iam_role_policy" "api_lambda" {
  name = "${var.project}-api-policy"
  role = aws_iam_role.api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = [for arn in var.log_group_arns : "${arn}:*"]
      },
      {
        Sid      = "SQSSendMessage"
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = var.sqs_queue_arn
      },
      {
        Sid    = "SSMGetParameters"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
        ]
        Resource = "arn:aws:ssm:*:*:parameter/${var.project}/*"
      },
      {
        Sid    = "XRayTracing"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
        ]
        Resource = "*"
      },
    ]
  })
}

# ── Worker Lambda Role ───────────────────────────────────────
resource "aws_iam_role" "worker_lambda" {
  name               = "${var.project}-${var.environment}-worker-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = { Name = "${var.project}-worker-lambda" }
}

resource "aws_iam_role_policy" "worker_lambda" {
  name = "${var.project}-worker-policy"
  role = aws_iam_role.worker_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = [for arn in var.log_group_arns : "${arn}:*"]
      },
      {
        Sid    = "SQSConsumeMessages"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = var.sqs_queue_arn
      },
      {
        Sid    = "SSMGetParameters"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
        ]
        Resource = "arn:aws:ssm:*:*:parameter/${var.project}/*"
      },
      {
        Sid    = "XRayTracing"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
        ]
        Resource = "*"
      },
    ]
  })
}

# ── Frontend Lambda Role ─────────────────────────────────────
resource "aws_iam_role" "frontend_lambda" {
  name               = "${var.project}-${var.environment}-frontend-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = { Name = "${var.project}-frontend-lambda" }
}

resource "aws_iam_role_policy" "frontend_lambda" {
  name = "${var.project}-frontend-policy"
  role = aws_iam_role.frontend_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = [for arn in var.log_group_arns : "${arn}:*"]
      },
    ]
  })
}
