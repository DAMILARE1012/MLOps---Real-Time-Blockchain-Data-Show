terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider configuration with LocalStack support
provider "aws" {
  region                      = var.aws_region
  access_key                  = var.aws_access_key
  secret_key                  = var.aws_secret_key
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  
  # LocalStack endpoints
  endpoints {
    s3             = var.localstack_endpoint
    rds            = var.localstack_endpoint
    ec2            = var.localstack_endpoint
    cloudwatch     = var.localstack_endpoint
    iam            = var.localstack_endpoint
    secretsmanager = var.localstack_endpoint
  }
}