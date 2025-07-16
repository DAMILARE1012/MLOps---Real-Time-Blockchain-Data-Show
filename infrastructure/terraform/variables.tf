variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_access_key" {
  description = "AWS access key"
  type        = string
  default     = "test"
}

variable "aws_secret_key" {
  description = "AWS secret key"
  type        = string
  default     = "test"
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL"
  type        = string
  default     = "http://localstack:4566"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "blockchain_ml"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "blockchain_user"
}

variable "db_password" {
  description = "Database password"
  type        = string
  default     = "blockchain_password"
  sensitive   = true
}

variable "ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
  default     = "ami-0c55b159cbfafe1d0"  # Amazon Linux 2
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "EC2 Key Pair name"
  type        = string
  default     = "blockchain-ml-key"
}

variable "telegram_token" {
  description = "Telegram bot token"
  type        = string
  default     = "dummy-token"
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}