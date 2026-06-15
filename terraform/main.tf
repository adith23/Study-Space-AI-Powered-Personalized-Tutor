terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # For production, store state in Terraform Cloud (free) or an S3 backend.
  # Local state is fine for a single-operator setup.
  # backend "s3" {
  #   bucket = "study-space-tf-state"
  #   key    = "production/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      FreeTier    = "always-free"
    }
  }
}

# ── Modules ──────────────────────────────────────────────────

module "ecr" {
  source  = "./modules/ecr"
  project = var.project_name
}

module "sqs" {
  source      = "./modules/sqs"
  environment = var.environment
  project     = var.project_name
}

module "monitoring" {
  source      = "./modules/monitoring"
  environment = var.environment
  project     = var.project_name
}

module "iam" {
  source          = "./modules/iam"
  environment     = var.environment
  project         = var.project_name
  sqs_queue_arn   = module.sqs.queue_arn
  log_group_arns  = module.monitoring.log_group_arns
  ecr_repo_arns   = [
    module.ecr.api_repo_arn,
    module.ecr.worker_repo_arn,
    module.ecr.frontend_repo_arn,
  ]
}

module "lambda" {
  source                  = "./modules/lambda"
  environment             = var.environment
  project                 = var.project_name
  aws_region              = var.aws_region
  api_image_uri           = var.api_image_uri
  worker_image_uri        = var.worker_image_uri
  frontend_image_uri      = var.frontend_image_uri
  api_execution_role      = module.iam.api_lambda_role_arn
  worker_execution_role   = module.iam.worker_lambda_role_arn
  frontend_execution_role = module.iam.frontend_lambda_role_arn
  sqs_queue_arn           = module.sqs.queue_arn
}

module "cloudfront" {
  source                = "./modules/cloudfront"
  environment           = var.environment
  project               = var.project_name
  api_function_url      = module.lambda.api_function_url
  frontend_function_url = module.lambda.frontend_function_url
}
