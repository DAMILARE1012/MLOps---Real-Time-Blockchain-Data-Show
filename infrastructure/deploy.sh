#!/bin/bash

# Blockchain ML Infrastructure Deployment Script
# This script deploys the infrastructure using LocalStack and Terraform

set -e

echo "🚀 Starting Blockchain ML Infrastructure Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it first."
    exit 1
fi

print_status "Starting LocalStack and infrastructure services..."

# Start LocalStack and related services
docker-compose up -d localstack postgres redis

# Wait for LocalStack to be ready
print_status "Waiting for LocalStack to be ready..."
timeout=60
counter=0
while ! curl -s http://localhost:4566/health > /dev/null; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        print_error "LocalStack failed to start within $timeout seconds"
        exit 1
    fi
done

print_status "LocalStack is ready!"

# Initialize Terraform
print_status "Initializing Terraform..."
docker-compose run --rm terraform terraform init

# Validate Terraform configuration
print_status "Validating Terraform configuration..."
docker-compose run --rm terraform terraform validate

# Plan infrastructure changes
print_status "Planning infrastructure changes..."
docker-compose run --rm terraform terraform plan -out=tfplan

# Apply infrastructure changes
print_status "Applying infrastructure changes..."
docker-compose run --rm terraform terraform apply -auto-approve tfplan

# Display outputs
print_status "Displaying infrastructure outputs..."
docker-compose run --rm terraform terraform output

# Verify AWS resources in LocalStack
print_status "Verifying created AWS resources..."

# Check S3 buckets
echo "S3 Buckets:"
aws --endpoint-url=http://localhost:4566 s3 ls

# Check RDS instances
echo "RDS Instances:"
aws --endpoint-url=http://localhost:4566 rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Engine]' --output table

# Check EC2 instances
echo "EC2 Instances:"
aws --endpoint-url=http://localhost:4566 ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType]' --output table

# Check CloudWatch log groups
echo "CloudWatch Log Groups:"
aws --endpoint-url=http://localhost:4566 logs describe-log-groups --query 'logGroups[*].logGroupName' --output table

# Check Secrets Manager
echo "Secrets Manager:"
aws --endpoint-url=http://localhost:4566 secretsmanager list-secrets --query 'SecretList[*].Name' --output table

print_status "Infrastructure deployment completed successfully! 🎉"
print_status "You can now access the following services:"
print_status "- LocalStack Dashboard: http://localhost:4566"
print_status "- Grafana: http://localhost:3000 (admin/admin)"
print_status "- Prometheus: http://localhost:9090"
print_status "- MLflow: http://localhost:5000"

echo ""
print_warning "To destroy the infrastructure, run: ./infrastructure/destroy.sh"
print_warning "To view infrastructure state, run: docker-compose run --rm terraform terraform show"