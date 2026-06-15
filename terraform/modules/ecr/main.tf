# ECR Public repositories (Always Free: 50 GB storage)
# ECR Public is only available in us-east-1

resource "aws_ecrpublic_repository" "api" {
  repository_name = "${var.project}-api"

  catalog_data {
    description       = "Study Space — Backend API Lambda image"
    operating_systems = ["Linux"]
    architectures     = ["x86-64"]
  }

  tags = { Name = "${var.project}-api" }
}

resource "aws_ecrpublic_repository" "worker" {
  repository_name = "${var.project}-worker"

  catalog_data {
    description       = "Study Space — Worker Lambda image (SQS-triggered)"
    operating_systems = ["Linux"]
    architectures     = ["x86-64"]
  }

  tags = { Name = "${var.project}-worker" }
}

resource "aws_ecrpublic_repository" "frontend" {
  repository_name = "${var.project}-frontend"

  catalog_data {
    description       = "Study Space — Frontend Lambda image (Next.js)"
    operating_systems = ["Linux"]
    architectures     = ["x86-64"]
  }

  tags = { Name = "${var.project}-frontend" }
}
