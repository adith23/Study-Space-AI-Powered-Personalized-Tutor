output "api_function_url" {
  description = "API Lambda Function URL"
  value       = aws_lambda_function_url.api.function_url
}

output "frontend_function_url" {
  description = "Frontend Lambda Function URL"
  value       = aws_lambda_function_url.frontend.function_url
}

output "api_function_name" {
  value = aws_lambda_function.api.function_name
}

output "worker_function_name" {
  value = aws_lambda_function.worker.function_name
}

output "frontend_function_name" {
  value = aws_lambda_function.frontend.function_name
}
