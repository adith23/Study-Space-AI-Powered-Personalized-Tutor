output "log_group_arns" {
  description = "ARNs of all Lambda log groups"
  value       = [for lg in aws_cloudwatch_log_group.lambda : lg.arn]
}

output "log_group_names" {
  description = "Names of all Lambda log groups"
  value       = [for lg in aws_cloudwatch_log_group.lambda : lg.name]
}
