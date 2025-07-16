#!/bin/bash

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Python 3.10
yum install -y python3 python3-pip

# Install AWS CLI
pip3 install awscli

# Create application directory
mkdir -p /opt/blockchain-ml
cd /opt/blockchain-ml

# Clone the repository (in production, you'd use a proper deployment mechanism)
# For now, we'll create a basic deployment structure
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  blockchain-ml:
    image: blockchain-ml:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://blockchain_user:blockchain_password@${db_endpoint}/blockchain_ml
      - S3_BUCKET=${s3_bucket}
      - AWS_DEFAULT_REGION=us-east-1
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    restart: unless-stopped

  mlflow:
    image: python:3.10-slim
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_TRACKING_URI=sqlite:///mlflow.db
    command: >
      bash -c "pip install mlflow &&
               mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db"
    restart: unless-stopped
EOF

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Setup log rotation
cat > /etc/logrotate.d/blockchain-ml << 'EOF'
/var/log/blockchain-ml/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

# Create systemd service for auto-start
cat > /etc/systemd/system/blockchain-ml.service << 'EOF'
[Unit]
Description=Blockchain ML Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/blockchain-ml
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl enable blockchain-ml.service
systemctl start blockchain-ml.service

echo "Blockchain ML deployment completed successfully!"