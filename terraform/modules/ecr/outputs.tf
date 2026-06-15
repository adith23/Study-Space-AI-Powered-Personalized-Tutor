output "api_repo_uri" {
  description = "Private ECR URI for the API image"
  value       = aws_ecr_repository.api.repository_url
}

output "worker_repo_uri" {
  description = "Private ECR URI for the Worker image"
  value       = aws_ecr_repository.worker.repository_url
}

output "frontend_repo_uri" {
  description = "Private ECR URI for the Frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

output "api_repo_arn" {
  description = "ARN of the API ECR repository"
  value       = aws_ecr_repository.api.arn
}

output "worker_repo_arn" {
  description = "ARN of the Worker ECR repository"
  value       = aws_ecr_repository.worker.arn
}

output "frontend_repo_arn" {
  description = "ARN of the Frontend ECR repository"
  value       = aws_ecr_repository.frontend.arn
}
