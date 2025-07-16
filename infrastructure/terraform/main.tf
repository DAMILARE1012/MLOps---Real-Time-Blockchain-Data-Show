# Configure the AWS Provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = var.aws_access_key
  secret_key                  = var.aws_secret_key
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  
  # LocalStack configuration
  endpoints {
    s3             = var.localstack_endpoint
    rds            = var.localstack_endpoint
    ec2            = var.localstack_endpoint
    cloudwatch     = var.localstack_endpoint
    iam            = var.localstack_endpoint
    secretsmanager = var.localstack_endpoint
  }
}

# S3 bucket for model artifacts and data storage
resource "aws_s3_bucket" "model_artifacts" {
  bucket = "blockchain-ml-model-artifacts"
}

resource "aws_s3_bucket" "data_storage" {
  bucket = "blockchain-ml-data-storage"
}

resource "aws_s3_bucket_versioning" "model_artifacts_versioning" {
  bucket = aws_s3_bucket.model_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM role for EC2 instances
resource "aws_iam_role" "blockchain_ml_role" {
  name = "blockchain-ml-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for S3 access
resource "aws_iam_policy" "s3_access_policy" {
  name        = "blockchain-ml-s3-access"
  description = "Policy for accessing S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.model_artifacts.arn,
          "${aws_s3_bucket.model_artifacts.arn}/*",
          aws_s3_bucket.data_storage.arn,
          "${aws_s3_bucket.data_storage.arn}/*"
        ]
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "s3_policy_attachment" {
  role       = aws_iam_role.blockchain_ml_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

# Instance profile for EC2
resource "aws_iam_instance_profile" "blockchain_ml_profile" {
  name = "blockchain-ml-profile"
  role = aws_iam_role.blockchain_ml_role.name
}

# Security group for the application
resource "aws_security_group" "blockchain_ml_sg" {
  name        = "blockchain-ml-security-group"
  description = "Security group for blockchain ML application"

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS instance for PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier = "blockchain-ml-postgres"
  
  engine            = "postgres"
  engine_version    = "13.13"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_type      = "gp2"
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.blockchain_ml_sg.id]
  
  skip_final_snapshot = true
  
  tags = {
    Name = "blockchain-ml-database"
  }
}

# EC2 instance for the application
resource "aws_instance" "blockchain_ml_app" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name              = var.key_name
  vpc_security_group_ids = [aws_security_group.blockchain_ml_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.blockchain_ml_profile.name
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    db_endpoint = aws_db_instance.postgres.endpoint
    s3_bucket   = aws_s3_bucket.model_artifacts.bucket
  }))
  
  tags = {
    Name = "blockchain-ml-application"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "blockchain_ml_logs" {
  name              = "/aws/blockchain-ml/application"
  retention_in_days = 7
}

# Secrets Manager for sensitive configuration
resource "aws_secretsmanager_secret" "blockchain_ml_secrets" {
  name = "blockchain-ml-secrets"
}

resource "aws_secretsmanager_secret_version" "blockchain_ml_secrets" {
  secret_id = aws_secretsmanager_secret.blockchain_ml_secrets.id
  secret_string = jsonencode({
    db_password = var.db_password
    telegram_token = var.telegram_token
  })
}