# Blockchain ML - End-to-End ML System

A comprehensive machine learning system for real-time blockchain data analysis using the Blockchain.info WebSocket API.

## 🚀 Features

- **Real-time Data Pipeline**: WebSocket connection to Blockchain.info API
- **ML Model Development**: Anomaly detection, transaction classification, price prediction
- **Feature Engineering**: Automated feature extraction and storage
- **Model Serving**: FastAPI-based inference API
- **Monitoring**: Real-time model performance and system metrics
- **CI/CD**: Automated testing, building, and deployment
- **Infrastructure**: Docker, Kubernetes, AWS ready

## 🏗️ Architecture

```
WebSocket API → Data Pipeline → Feature Store → ML Models → API → Monitoring
     ↓              ↓              ↓            ↓         ↓         ↓
Blockchain    Real-time      Feast Store   MLflow    FastAPI   Prometheus
   Data       Processing     Features      Models    Serving   + Grafana
```

## 📋 Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL
- Redis
- AWS Account (for production deployment)

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd blockchain-ml
```

### 2. Install dependencies
```bash
# Install production dependencies
make install

# Install development dependencies
make install-dev
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Start services with Docker
```bash
make docker-run
```

## 🚀 Quick Start

### 1. Start the data pipeline
```bash
make run-pipeline
```

### 2. Run model training
```bash
make run-training
```

### 3. Start the API server
```bash
make run-api
```

### 4. Access the services
- **API**: http://localhost:8000
- **MLflow**: http://localhost:5000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## 📁 Project Structure

```
blockchain-ml/
├── src/                    # Source code
│   ├── data_pipeline/     # WebSocket client, data processing
│   ├── feature_engineering/ # Feature extraction, feature store
│   ├── models/            # ML model definitions and training
│   ├── api/               # FastAPI application
│   ├── monitoring/        # Monitoring and observability
│   └── workflows/         # Prefect workflows
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── infrastructure/        # Infrastructure as code
│   ├── terraform/        # AWS infrastructure
│   ├── docker/           # Docker configurations
│   └── kubernetes/       # K8s manifests
├── docs/                 # Documentation
├── notebooks/            # Jupyter notebooks
└── scripts/              # Utility scripts
```

## 🔧 Development

### Running tests
```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e
```

### Code quality
```bash
# Format code
make format

# Run linting
make lint
```

### Docker operations
```bash
# Build image
make docker-build

# Start services
make docker-run

# Stop services
make docker-stop

# View logs
make docker-logs
```

## 📊 ML Models

### 1. Anomaly Detection
- **Purpose**: Detect unusual transaction patterns
- **Features**: Transaction size, frequency, address patterns
- **Algorithm**: Isolation Forest, One-Class SVM, Local Outlier Factor

### 2. Transaction Classification
- **Purpose**: Classify transactions by type (exchange, retail, mining)
- **Features**: Address behavior, transaction patterns
- **Algorithm**: Random Forest, XGBoost

### 3. Price Impact Prediction
- **Purpose**: Predict Bitcoin price impact of large transactions
- **Features**: Transaction size, market conditions, network metrics
- **Algorithm**: XGBoost, Random Forest, Linear Regression

## 🔍 Monitoring

### Model Performance
- **Evidently**: Model drift detection
- **MLflow**: Experiment tracking
- **Custom metrics**: Business-specific KPIs

### System Metrics
- **Prometheus**: System monitoring
- **Grafana**: Dashboards and alerts
- **Health checks**: Service availability

## 🚀 Deployment

### Local Development
```bash
make docker-run
```

### Production (AWS)
```bash
# Deploy infrastructure (EC2, RDS, S3)
cd infrastructure/terraform
terraform init
terraform apply

# Deploy application
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 API Endpoints

### Health Check
```bash
GET /health
```

### Model Inference
```bash
POST /predict/anomaly
POST /predict/classification
POST /predict/price-impact
```

### Monitoring
```bash
GET /metrics
GET /model/performance
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

## 🗺️ Roadmap

- [ ] Advanced ML models (Transformer-based)
- [ ] Real-time alerting system
- [ ] Multi-chain support (Ethereum, Solana)
- [ ] Advanced analytics dashboard
- [ ] Mobile app for alerts
- [ ] Enterprise features 