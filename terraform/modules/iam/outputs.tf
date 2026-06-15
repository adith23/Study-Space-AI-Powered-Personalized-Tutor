output "api_lambda_role_arn" {
  value = aws_iam_role.api_lambda.arn
}

output "worker_lambda_role_arn" {
  value = aws_iam_role.worker_lambda.arn
}

output "frontend_lambda_role_arn" {
  value = aws_iam_role.frontend_lambda.arn
}
