output "cloudfront_url" {
  description = "CloudFront distribution URL (primary access point)"
  value       = "https://${module.cloudfront.distribution_domain}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = module.cloudfront.distribution_id
}

output "api_function_url" {
  description = "Backend API Lambda Function URL (direct access)"
  value       = module.lambda.api_function_url
}

output "frontend_function_url" {
  description = "Frontend Lambda Function URL (direct access)"
  value       = module.lambda.frontend_function_url
}

output "sqs_queue_url" {
  description = "SQS task queue URL (for SSM parameter seeding)"
  value       = module.sqs.queue_url
}

output "sqs_dlq_url" {
  description = "SQS dead-letter queue URL"
  value       = module.sqs.dlq_url
}

output "ecr_api_repo" {
  description = "ECR Public repository URI for API image"
  value       = module.ecr.api_repo_uri
}

output "ecr_worker_repo" {
  description = "ECR Public repository URI for Worker image"
  value       = module.ecr.worker_repo_uri
}

output "ecr_frontend_repo" {
  description = "ECR Public repository URI for Frontend image"
  value       = module.ecr.frontend_repo_uri
}
