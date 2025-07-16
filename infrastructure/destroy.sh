#!/bin/bash

# Blockchain ML Infrastructure Destruction Script
# This script destroys the infrastructure created by LocalStack and Terraform

set -e

echo "🗑️ Starting Blockchain ML Infrastructure Destruction"

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

# Confirm destruction
read -p "Are you sure you want to destroy the infrastructure? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_status "Destruction cancelled."
    exit 0
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Destroying Terraform infrastructure..."

# Destroy infrastructure
docker-compose run --rm terraform terraform destroy -auto-approve

print_status "Stopping and removing Docker containers..."

# Stop all services
docker-compose down

# Remove volumes (optional - uncomment if you want to remove data)
# print_warning "Removing Docker volumes..."
# docker-compose down -v

print_status "Cleaning up Terraform state..."

# Remove Terraform state files (optional)
rm -f infrastructure/terraform/terraform.tfstate*
rm -f infrastructure/terraform/tfplan
rm -rf infrastructure/terraform/.terraform/

print_status "Infrastructure destroyed successfully! 🧹"
print_status "All AWS resources have been removed from LocalStack"
print_status "Docker containers have been stopped and removed"