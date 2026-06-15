output "api_repo_uri" {
  value = aws_ecrpublic_repository.api.repository_uri
}

output "worker_repo_uri" {
  value = aws_ecrpublic_repository.worker.repository_uri
}

output "frontend_repo_uri" {
  value = aws_ecrpublic_repository.frontend.repository_uri
}
