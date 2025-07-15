# 🤖 Blockchain Anomaly Detection - Automation System

This comprehensive automation system provides production-ready workflows for monitoring, maintaining, and improving your blockchain anomaly detection system using **Prefect** as the orchestration engine.

## 🚀 Features

### 1. **Health Monitoring** (`automation/flows/health_monitoring.py`)
- **Frequency**: Every 15 minutes
- **Monitors**: Pipeline health, model performance, database connectivity, alert systems
- **Alerts**: Telegram notifications for system issues
- **Reports**: JSON health reports with detailed metrics

### 2. **System Monitoring** (`automation/flows/system_monitoring.py`)
- **Frequency**: Every 5 minutes
- **Monitors**: CPU, memory, disk usage, network I/O, processing rates
- **Features**: Auto-restart on critical failures, performance metrics
- **Alerts**: Resource utilization and performance alerts

### 3. **Automated Model Retraining** (`automation/flows/model_retraining.py`)
- **Frequency**: Daily at 2:00 AM
- **Features**: Data drift detection, performance evaluation, A/B testing
- **Validation**: Automated model validation before deployment
- **Rollback**: Automatic rollback on validation failure

### 4. **CI/CD Pipeline** (`automation/deployments/deploy_flows.py`)
- **Triggers**: Manual or git-based deployment
- **Testing**: Automated test suite execution
- **Deployment**: Zero-downtime model deployment
- **Rollback**: Automatic rollback on failure

## 📋 Prerequisites

### Required Dependencies
```bash
pip install prefect pandas numpy scikit-learn psutil asyncpg redis python-telegram-bot
```

### Environment Variables
Create a `.env` file with:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### System Requirements
- **Python**: 3.8+
- **Memory**: 4GB+ RAM
- **Storage**: 10GB+ free space
- **Network**: Internet connectivity for Telegram alerts

## 🔧 Quick Start

### 1. **Automatic Setup** (Recommended)
```bash
# Start everything automatically
python start_automation.py
```

This will:
- ✅ Check dependencies and environment
- ✅ Start Prefect server
- ✅ Deploy all workflows
- ✅ Start Prefect agent
- ✅ Run initial health check
- ✅ Show status dashboard

### 2. **Manual Setup**
```bash
# Start Prefect server
prefect server start

# Deploy workflows (in another terminal)
python automation/deployments/deploy_flows.py

# Start Prefect agent
prefect agent start --work-pool default-agent-pool
```

## 🖥️ Management Interface

### Interactive Menu
```bash
python automation/run_automation.py --action interactive
```

### Command Line Interface
```bash
# Check system status
python automation/run_automation.py --action status

# Run health check manually
python automation/run_automation.py --action health

# Run system monitoring
python automation/run_automation.py --action monitor

# Trigger model retraining
python automation/run_automation.py --action retrain

# Deploy workflows
python automation/run_automation.py --action deploy
```

## 📊 Monitoring Dashboard

### Prefect UI
- **URL**: http://localhost:4200
- **Features**: 
  - Real-time workflow status
  - Execution history
  - Performance metrics
  - Error tracking
  - Scheduling management

### System Status
```bash
python automation/run_automation.py --action status
```

**Output Example:**
```
📊 Automation Status Dashboard
==================================================
🔧 Configuration:
  • Automation enabled: True
  • Telegram notifications: True

📁 File Status:
  ✅ models/anomaly_model.pkl (2.1 MB, modified: 2024-01-15 14:30:15)
  ✅ anomaly_events.csv (42 KB, modified: 2024-01-15 14:35:22)
  ✅ whale_events.csv (53 KB, modified: 2024-01-15 14:35:20)
  ✅ data_pipeline.log (1.8 MB, modified: 2024-01-15 14:35:25)

🏥 System Health:
  ✅ Data pipeline: Active (last update: 5s ago)
  📊 Anomaly events: 337 total
  🐋 Whale events: 421 total
```

## 🔔 Alert System

### Telegram Notifications

**Health Alerts** (Every 15 minutes if issues detected):
```
🚨 SYSTEM HEALTH ALERT 🚨

Overall Status: WARNING
Health Score: 65%

Component Status:
🔄 Pipeline: 75%
🤖 Model: 50%
🗄️ Database: 80%
📱 Alerts: 55%

Time: 2024-01-15T14:35:00

Please check the system immediately!
```

**Monitoring Alerts** (Every 5 minutes or on issues):
```
⚠️ SYSTEM MONITORING SUMMARY ⚠️

Status: ALERTS DETECTED

System Resources:
🖥️ CPU: 85.2%
💾 Memory: 78.3%
💽 Disk: 45.1%

Pipeline Metrics:
⚡ Processing Rate: 15.2/min
🚨 Anomalies (1h): 12
🐋 Whales (1h): 3
❌ Error Rate: 2.1%

Active Alerts:
⚠️ HIGH CPU: 85.2%
⚠️ HIGH ERROR RATE: 2.1%

⏰ Time: 2024-01-15 14:35:00
```

**Model Retraining** (Daily or on-demand):
```
🤖 MODEL RETRAINING COMPLETED 🤖

✅ Status: Successfully deployed new model
📊 Performance:
  • Accuracy: 94.2%
  • Precision: 87.5%
  • Recall: 91.3%
  • F1 Score: 89.4%

📈 Training Data: 15,432 samples
🕒 Timestamp: 2024-01-15T02:00:00

The system is now using the updated model for anomaly detection.
```

## 🔄 Workflow Schedules

| Workflow | Schedule | Description |
|----------|----------|-------------|
| **Health Check** | `*/15 * * * *` | Every 15 minutes |
| **System Monitoring** | `*/5 * * * *` | Every 5 minutes |
| **Model Retraining** | `0 2 * * *` | Daily at 2:00 AM |
| **CI/CD Pipeline** | Manual | On-demand deployment |

## 📈 Performance Metrics

### Collected Metrics
- **System Resources**: CPU, Memory, Disk, Network I/O
- **Pipeline Performance**: Processing rate, error rate, latency
- **Model Performance**: Accuracy, precision, recall, F1 score
- **Data Quality**: Drift detection, anomaly rates, data freshness

### Historical Data
- **Location**: `monitoring_data/`
- **Format**: JSON Lines (JSONL)
- **Retention**: 30 days (configurable)
- **Analysis**: Trend analysis, performance regression detection

## 🛠️ Configuration

### Automation Config (`automation/config/automation_config.json`)
```json
{
  "enabled": true,
  "schedules": {
    "health_check": "*/15 * * * *",
    "system_monitoring": "*/5 * * * *",
    "model_retraining": "0 2 * * *"
  },
  "notifications": {
    "telegram_enabled": true,
    "email_enabled": false
  },
  "thresholds": {
    "cpu_alert": 80,
    "memory_alert": 85,
    "disk_alert": 90,
    "error_rate_alert": 0.1
  }
}
```

### Customize Thresholds
```bash
python automation/run_automation.py --action interactive
# Select "9. Configure Settings"
```

## 🔍 Troubleshooting

### Common Issues

**1. Prefect Server Not Starting**
```bash
# Check if port 4200 is available
netstat -an | grep 4200

# Kill existing processes
pkill -f "prefect server"

# Restart with specific port
prefect server start --host 0.0.0.0 --port 4200
```

**2. Agent Not Processing Flows**
```bash
# Check work pools
prefect work-pool ls

# Create work pool if missing
prefect work-pool create --type process default-agent-pool

# Restart agent
prefect agent start --work-pool default-agent-pool
```

**3. Telegram Alerts Not Working**
```bash
# Test Telegram connection
python -c "
from automation.flows.health_monitoring import check_alert_system_health
import asyncio
result = asyncio.run(check_alert_system_health())
print(result)
"
```

**4. Model Retraining Failures**
```bash
# Check training data availability
python -c "
import pandas as pd
print('Anomaly events:', len(pd.read_csv('anomaly_events.csv')) if os.path.exists('anomaly_events.csv') else 0)
print('Whale events:', len(pd.read_csv('whale_events.csv')) if os.path.exists('whale_events.csv') else 0)
"
```

### Debug Mode
```bash
# Enable debug logging
export PREFECT_LOGGING_LEVEL=DEBUG

# Run flows with detailed logging
python automation/run_automation.py --action health
```

## 📊 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Start automation
CMD ["python", "start_automation.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blockchain-anomaly-automation
spec:
  replicas: 1
  selector:
    matchLabels:
      app: blockchain-anomaly-automation
  template:
    metadata:
      labels:
        app: blockchain-anomaly-automation
    spec:
      containers:
      - name: automation
        image: blockchain-anomaly-detection:latest
        env:
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: telegram-secret
              key: token
        - name: TELEGRAM_CHAT_ID
          valueFrom:
            secretKeyRef:
              name: telegram-secret
              key: chat_id
```

### System Service (Linux)
```ini
[Unit]
Description=Blockchain Anomaly Detection Automation
After=network.target

[Service]
Type=simple
User=blockchain
WorkingDirectory=/opt/blockchain-anomaly-detection
ExecStart=/usr/bin/python3 start_automation.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/blockchain-anomaly-detection

[Install]
WantedBy=multi-user.target
```

## 🔐 Security Considerations

### Environment Variables
- Store sensitive data in environment variables
- Use secrets management systems in production
- Rotate API keys regularly

### Network Security
- Restrict Prefect UI access (use reverse proxy)
- Enable HTTPS for production deployments
- Use VPN for remote access

### Data Protection
- Encrypt sensitive data at rest
- Use secure connections for database access
- Implement proper access controls

## 📚 API Reference

### Health Check Flow
```python
from automation.flows.health_monitoring import system_health_check_flow
result = await system_health_check_flow()
```

### System Monitoring Flow
```python
from automation.flows.system_monitoring import system_monitoring_flow
result = await system_monitoring_flow()
```

### Model Retraining Flow
```python
from automation.flows.model_retraining import automated_model_retraining_flow
result = await automated_model_retraining_flow()
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-automation`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

## 📄 License

This automation system is part of the Blockchain Anomaly Detection project.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Prefect logs: `prefect server logs`
3. Test individual components manually
4. Contact system administrator

---

**🎉 Your blockchain anomaly detection system is now fully automated and production-ready!**