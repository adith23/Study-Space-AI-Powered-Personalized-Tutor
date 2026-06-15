output "queue_arn" {
  value = aws_sqs_queue.tasks.arn
}

output "queue_url" {
  value = aws_sqs_queue.tasks.url
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.url
}
