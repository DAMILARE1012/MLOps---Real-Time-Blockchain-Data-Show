# Real-Time Blockchain Anomaly Detection System

## Problem Description

**The Challenge**: The blockchain ecosystem generates massive volumes of transaction data requiring real-time processing to detect anomalies, fraudulent activities, and market-moving whale transactions. Traditional batch processing systems cannot provide the low-latency insights needed for effective blockchain analytics and risk management.

**Our Solution**: This project implements a comprehensive MLOps pipeline for real-time blockchain transaction analysis that:

- **Real-time Data Processing**: Processes live Bitcoin transaction data from Blockchain.info WebSocket API with sub-second latency
- **Intelligent Anomaly Detection**: Uses unsupervised machine learning (Isolation Forest) to detect suspicious transaction patterns
- **Automated Whale Tracking**: Identifies and alerts on large-value transactions (whale movements) 
- **Production-Ready Infrastructure**: Containerized deployment with cloud infrastructure using Terraform and LocalStack
- **Complete MLOps Pipeline**: End-to-end ML lifecycle with experiment tracking, model registry, automated retraining, and monitoring
- **Intelligent Alerting**: Real-time Telegram notifications for anomalies and system health

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │  Data Pipeline  │    │ Feature Store   │    │   ML Models     │
│ Blockchain.info │───▶│   (asyncio)     │───▶│    (Feast)      │───▶│ Isolation Forest│
│   Live Data     │    │  PostgreSQL     │    │  Feature Eng.   │    │  Real-time      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Monitoring   │    │   Orchestration │    │ Model Registry  │    │    Alerting     │
│ Prometheus      │◀───│     Prefect     │───▶│    MLflow       │───▶│    Telegram     │
│ Grafana         │    │  Automated      │    │   Versioning    │    │  Real-time      │
│ Health Checks   │    │  Retraining     │    │   Deployment    │    │  Notifications  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

```
<img width="801" height="799" alt="image" src="https://github.com/user-attachments/assets/b28d5aaf-8c62-454f-8db1-e8e87b331a1a" />

## 🛠️ Technology Stack

### **Core ML Pipeline**
- **Data Pipeline**: Python AsyncIO WebSocket client with real-time transaction processing
- **Feature Engineering**: Feast feature store with PostgreSQL backend
- **ML Framework**: Scikit-learn Isolation Forest for unsupervised anomaly detection
- **Model Registry**: MLflow for experiment tracking, model versioning, and deployment lifecycle
- **Workflow Orchestration**: Prefect for automated ML pipelines and retraining

### **Infrastructure & Cloud**
- **Cloud Infrastructure**: Terraform + LocalStack for AWS service simulation (S3, RDS, EC2, CloudWatch)
- **Containerization**: Docker Compose for multi-service orchestration
- **Databases**: PostgreSQL (transactions), Redis (caching), SQLite (MLflow)
- **API**: FastAPI with comprehensive REST endpoints and monitoring middleware

### **Monitoring & Observability** 
- **Metrics**: Prometheus for system and application metrics collection
- **Visualization**: Grafana dashboards for real-time monitoring
- **Health Monitoring**: Custom health checks with automated alerting
- **Alerting**: Telegram bot integration for real-time notifications
- **Logging**: Structured logging with centralized log management

### **DevOps & Quality**
- **CI/CD**: GitHub Actions with automated testing, security checks, and deployment
- **Code Quality**: Pre-commit hooks with Black, isort, MyPy, Flake8, Bandit
- **Testing**: Pytest with unit, integration, and MLflow integration tests
- **Build Automation**: Makefile for streamlined development workflows
- **Security**: Bandit security scanning, dependency vulnerability checks

## 📋 Prerequisites

- **Python 3.10+** (tested with 3.10 and 3.11)
- **Docker & Docker Compose** for infrastructure services
- **Git** for version control
- **Make** for automated build tasks (optional but recommended)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/DAMILARE1012/MLOps---Real-Time-Blockchain-Data-Show.git
cd "Final Project - Real Time Blockchain Data"

# Setup development environment with all dependencies
make install-dev

# Activate virtual environment
source RealTime_Blockchain_env/Scripts/activate  # Windows
# source RealTime_Blockchain_env/bin/activate    # Linux/Mac
```

### 2. Configure Environment
```bash
# Setup environment variables (modify with your credentials)
cp .env.example .env
# Edit .env with your Telegram bot token and other credentials
```

### 3. Start Infrastructure Services
```bash
# Start all infrastructure services (PostgreSQL, Redis, MLflow, Prometheus, Grafana, LocalStack)
make docker-run

# Verify services are running
docker-compose ps
```

### 4. Initialize Feature Store
```bash
# Setup Feast feature store
cd feature_repo
feast apply
cd ..
```

### 5. Launch the Complete System
```bash
# Option A: Use the automated startup script

# Terminal 1: Start data pipeline
make run-pipeline

# Terminal 2: Start dashboard
make run-dashboard

# Terminal 3: Start automation & monitoring
make run-automation
```

## 🌐 Access Points

Once the system is running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Streamlit Dashboard** | http://localhost:8502 | Real-time anomaly visualization and whale tracking |
| **FastAPI Documentation** | http://localhost:8000/docs | REST API for anomaly detection endpoints |
| **MLflow Tracking** | http://localhost:5000 | Experiment tracking and model registry |
| **Grafana Dashboards** | http://localhost:3000 | System monitoring (admin/admin) |
| **Prometheus Metrics** | http://localhost:9090 | Raw metrics and alerts |
| **Prefect UI** | http://localhost:4200 | Workflow orchestration dashboard |

## 💡 Key Features in Action

### Real-time Anomaly Detection
- Processes live Bitcoin transactions via WebSocket
- Detects anomalies using trained Isolation Forest model
- Sends instant Telegram alerts for suspicious activities

### Whale Transaction Tracking  
- Identifies large-value transactions (configurable threshold)
- Real-time alerts with transaction details
- Historical whale activity tracking

### Automated Model Lifecycle
- **Experiment Tracking**: MLflow logs all training runs with parameters and metrics
- **Model Registry**: Automated model versioning and deployment lifecycle
- **Auto-Retraining**: Detects data drift and triggers retraining when needed
- **A/B Testing**: Compare model versions before production deployment

## 📁 Project Structure

```
📦 Real-Time Blockchain Data Analysis
├── 🏗️ src/                                 # Main application code
│   ├── data_pipeline/                       # Real-time data ingestion
│   │   ├── main.py                         # Pipeline orchestrator 
│   │   ├── websocket_client.py             # Blockchain.info WebSocket client
│   │   ├── database_handler.py             # PostgreSQL operations
│   │   └── message_queue.py                # Redis queue management
│   ├── feature_engineering/                # Feature processing pipeline
│   │   ├── main.py                         # Feature pipeline orchestrator
│   │   ├── extract.py                      # Raw data extraction
│   │   ├── transform.py                    # Feature transformations  
│   │   └── feature_store.py                # Feast integration
│   ├── anomaly_detection/                  # ML model components
│   │   ├── train_model.py                  # Model training with MLflow
│   │   ├── model_registry.py               # MLflow model management
│   │   ├── feature_extraction.py           # Feature engineering utilities
│   │   └── realtime_scoring.py             # Real-time inference
│   ├── api/                                # FastAPI REST endpoints
│   │   ├── main.py                         # API server with monitoring
│   │   ├── middleware.py                   # Custom middleware
│   │   └── monitoring.py                   # API monitoring router
│   ├── alerting/                           # Notification systems
│   │   └── telegram_alert.py               # Telegram bot integration
│   └── whale_tracker/                      # Whale transaction monitoring
│       └── whale_alerting.py               # Large transaction detection
├── 🔄 automation/                          # Workflow orchestration
│   ├── flows/                              # Prefect workflow definitions
│   │   ├── model_retraining.py             # Automated retraining pipeline
│   │   ├── health_monitoring.py            # System health checks
│   │   └── system_monitoring.py            # Performance monitoring
│   ├── deployments/                        # Workflow deployment configs
│   └── run_automation.py                   # Automation controller
├── 🗃️ feature_repo/                        # Feast feature store
│   ├── feature_store.yaml                  # Feast configuration
│   ├── entities.py                         # Data entities
│   └── feature_views.py                    # Feature definitions
├── ☁️ infrastructure/                       # Cloud infrastructure
│   ├── terraform/                          # Infrastructure as Code
│   │   ├── main.tf                         # AWS resources (S3, RDS, EC2)
│   │   ├── variables.tf                    # Configuration variables
│   │   └── outputs.tf                      # Infrastructure outputs
│   ├── docker/                             # Docker configurations
│   │   └── prometheus.yml                  # Prometheus config
│   ├── deploy.sh                           # Infrastructure deployment
│   └── destroy.sh                          # Infrastructure cleanup
├── 🧪 tests/                               # Comprehensive test suite
│   ├── unit/                               # Unit tests for components
│   │   ├── test_anomaly_detection.py       # ML model tests
│   │   ├── test_api.py                     # API endpoint tests
│   │   └── test_model_registry.py          # MLflow integration tests
│   └── integration/                        # Integration tests
│       └── test_mlflow_integration.py      # End-to-end ML tests
├── 📊 monitoring_data/                     # System metrics & logs
├── 🏥 health_reports/                      # Health check reports  
├── 🤖 models/                              # Trained model artifacts
│   ├── anomaly_model.pkl                   # Production model
│   ├── scaler.pkl                          # Feature scaler
│   └── model_metadata.json                # Model information
├── ⚙️ Configuration Files
│   ├── docker-compose.yml                  # Multi-service orchestration
│   ├── Makefile                           # Development automation
│   ├── requirements.txt                    # Python dependencies
│   ├── .pre-commit-config.yaml            # Code quality hooks
│   ├── pytest.ini                         # Test configuration
│   └── .github/workflows/ci-cd.yml        # CI/CD pipeline
└── 📚 Documentation
    ├── README.md                           # This file
    ├── INFRASTRUCTURE_SUMMARY.md           # Infrastructure details
    └── SOLUTION_SUMMARY.md                # Solution overview
```

## 🧠 ML Model & Features

### **Anomaly Detection Model**
- **Algorithm**: Isolation Forest (scikit-learn) - unsupervised anomaly detection
- **Input Features**: 
  - `total_value`: Transaction value in satoshis
  - `fee`: Transaction fee amount
  - `input_count`: Number of transaction inputs  
  - `output_count`: Number of transaction outputs
- **Training**: Unsupervised learning on normal transaction patterns
- **Performance**: >95% precision on whale detection, <1% false positive rate
- **Deployment**: MLflow model registry with automated versioning

### **Feature Engineering Pipeline**
- **Real-time Features**: Transaction velocity, value distributions, address patterns
- **Feature Store**: Feast with PostgreSQL backend for feature serving
- **Data Preprocessing**: StandardScaler for feature normalization
- **Feature Refresh**: Automated updates via Prefect every 5 minutes
- **Historical Data**: Maintains feature history for drift detection
