# ── API Lambda (FastAPI backend) ──────────────────────────────
# Uses Lambda Web Adapter — FastAPI runs unchanged inside a container.
# Function URL provides a free HTTPS endpoint (no API Gateway needed).
# Always Free: 1M requests + 400,000 GB-s compute/month.

resource "aws_lambda_function" "api" {
  function_name = "${var.project}-${var.environment}-api"
  role          = var.api_execution_role
  package_type  = "Image"
  image_uri     = var.api_image_uri
  timeout       = 300 # 5 minutes for heavy AI requests
  memory_size   = 512 # Minimum for FastAPI + LangChain cold start

  ephemeral_storage {
    size = 2048 # 2 GB /tmp for document processing
  }

  environment {
    variables = {
      ENVIRONMENT  = var.environment
      AWS_LWA_PORT = "8000"
    }
  }

  tracing_config {
    mode = "Active" # X-Ray (Always Free: 100,000 traces/month)
  }

  tags = { Name = "${var.project}-api" }
}

# API Lambda Function URL (free — no API Gateway charges)
resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE" # Public (CORS handled by FastAPI middleware)

  cors {
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers     = ["*"]
    expose_headers    = ["*"]
    max_age           = 86400
    allow_credentials = true
  }
}

# ── Worker Lambda (SQS-triggered background tasks) ───────────
# Processes document embedding, quiz/flashcard generation, video rendering.
# Triggered by SQS — no HTTP endpoint needed.

resource "aws_lambda_function" "worker" {
  function_name = "${var.project}-${var.environment}-worker"
  role          = var.worker_execution_role
  package_type  = "Image"
  image_uri     = var.worker_image_uri
  timeout       = 900  # 15 min max (video rendering can be long)
  memory_size   = 1024 # More memory for Docling/LangChain

  ephemeral_storage {
    size = 10240 # 10 GB /tmp for video generation workspace
  }

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = { Name = "${var.project}-worker" }
}

# SQS → Worker Lambda trigger
resource "aws_lambda_event_source_mapping" "worker_sqs" {
  event_source_arn                   = var.sqs_queue_arn
  function_name                      = aws_lambda_function.worker.arn
  batch_size                         = 1 # Process one task at a time
  maximum_batching_window_in_seconds = 0 # No batching delay
  enabled                            = true

  scaling_config {
    maximum_concurrency = 5 # Stay within Lambda free tier concurrency
  }
}

# ── Frontend Lambda (Next.js SSR) ────────────────────────────
# Standalone Next.js build served via Lambda Web Adapter.

resource "aws_lambda_function" "frontend" {
  function_name = "${var.project}-${var.environment}-frontend"
  role          = var.frontend_execution_role
  package_type  = "Image"
  image_uri     = var.frontend_image_uri
  timeout       = 30  # SSR pages should render fast
  memory_size   = 256 # Lightweight for SSR

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      AWS_LWA_PORT             = "3000"
      NEXT_PUBLIC_API_BASE_URL = "PLACEHOLDER" # Set after CloudFront is created
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = { Name = "${var.project}-frontend" }
}

# Frontend Lambda Function URL
resource "aws_lambda_function_url" "frontend" {
  function_name      = aws_lambda_function.frontend.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "HEAD"]
    allow_headers = ["*"]
    max_age       = 86400
  }
}

# ── Provisioned Concurrency (optional, costs $) ─────────────
# Uncomment only if cold starts are unacceptable. Not free tier.
# resource "aws_lambda_provisioned_concurrency_config" "api" {
#   function_name                  = aws_lambda_function.api.function_name
#   provisioned_concurrent_executions = 1
#   qualifier                      = aws_lambda_function.api.version
# }

# ── API Invoke Config (no retries for HTTP requests) ─────────
resource "aws_lambda_function_event_invoke_config" "api" {
  function_name          = aws_lambda_function.api.function_name
  maximum_retry_attempts = 0 # Don't retry API requests (prevents duplicate processing)
}

# ── Reserved Concurrency (free tier safety) ──────────────────
# Limits maximum concurrent executions to stay within free tier.
# Lambda free tier: 1M requests + 400K GB-sec. These limits
# prevent runaway usage if traffic unexpectedly spikes.
resource "aws_lambda_function_event_invoke_config" "worker" {
  function_name          = aws_lambda_function.worker.function_name
  maximum_retry_attempts = 2 # Allow 2 retries for failed tasks (before DLQ)
}

