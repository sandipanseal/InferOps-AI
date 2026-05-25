# InferOps AI — AWS infrastructure root.
#
# Provisions every resource needed for the aws-deploy branch live demo:
#   - ECR repo for the FastAPI Lambda container image
#   - API Lambda (Mangum) + SQS worker Lambda (same image, different CMD)
#   - HTTP API Gateway v2 fronting the API Lambda
#   - SQS main + DLQ queues for async log + trace fan-out
#   - S3 + CloudFront for the Next.js static frontend
#   - IAM roles & policies wiring it all up
#
# Run order:
#   1. ./bootstrap.sh                       (one-time — creates the state bucket)
#   2. terraform init
#   3. terraform plan  -var-file="aws-deploy.tfvars"
#   4. terraform apply -var-file="aws-deploy.tfvars"

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # State lives in S3. The bucket must exist before `terraform init` —
  # bootstrap.sh creates it.
  backend "s3" {
    bucket  = "inferops-terraform-state"
    key     = "aws-deploy/terraform.tfstate"
    region  = "eu-central-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "inferops-ai"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
