output "s3_model_artifacts_bucket" {
  description = "S3 bucket for model artifacts"
  value       = aws_s3_bucket.model_artifacts.bucket
}

output "s3_data_storage_bucket" {
  description = "S3 bucket for data storage"
  value       = aws_s3_bucket.data_storage.bucket
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "ec2_public_ip" {
  description = "Public IP of EC2 instance"
  value       = aws_instance.blockchain_ml_app.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.blockchain_ml_app.id
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.blockchain_ml_sg.id
}

output "iam_role_arn" {
  description = "IAM role ARN"
  value       = aws_iam_role.blockchain_ml_role.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.blockchain_ml_logs.name
}

output "secrets_manager_arn" {
  description = "Secrets Manager ARN"
  value       = aws_secretsmanager_secret.blockchain_ml_secrets.arn
}

output "application_urls" {
  description = "Application access URLs"
  value = {
    api      = "http://${aws_instance.blockchain_ml_app.public_ip}:8000"
    grafana  = "http://${aws_instance.blockchain_ml_app.public_ip}:3000"
    mlflow   = "http://${aws_instance.blockchain_ml_app.public_ip}:5000"
    prometheus = "http://${aws_instance.blockchain_ml_app.public_ip}:9090"
  }
}