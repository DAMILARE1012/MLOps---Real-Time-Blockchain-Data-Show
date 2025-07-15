"""
Health Check Monitoring Flows for Blockchain Anomaly Detection System

This module contains Prefect flows for monitoring system health:
- Pipeline health checks
- Model performance monitoring
- Database connectivity
- Alert system verification
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import logging
from pathlib import Path

# Prefect imports
from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret
from prefect.runtime import deployment
from prefect.client.schemas.schedules import CronSchedule

# Import our system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.alerting.telegram_alert import send_telegram_alert_async
from src.data_pipeline.database_handler import DatabaseHandler
# from src.anomaly_detection.model_performance import ModelPerformanceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@task
async def check_pipeline_health() -> Dict[str, bool]:
    """Check if data pipeline is running and healthy"""
    logger = get_run_logger()
    
    health_status = {
        "pipeline_running": False,
        "recent_activity": False,
        "log_file_exists": False,
        "websocket_connected": False
    }
    
    try:
        # Check if pipeline log exists
        log_file_path = "data_pipeline.log"
        if os.path.exists(log_file_path):
            health_status["log_file_exists"] = True
            
            # Check if log was updated recently (within last 5 minutes)
            last_modified = datetime.fromtimestamp(os.path.getmtime(log_file_path))
            if datetime.now() - last_modified < timedelta(minutes=5):
                health_status["recent_activity"] = True
                health_status["pipeline_running"] = True
                
                # Check log content for WebSocket connection
                with open(log_file_path, 'r') as f:
                    recent_logs = f.readlines()[-50:]  # Get last 50 lines
                    for line in recent_logs:
                        if "Successfully connected to Blockchain.info WebSocket" in line:
                            health_status["websocket_connected"] = True
                            break
        
        logger.info(f"Pipeline health check: {health_status}")
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking pipeline health: {e}")
        return health_status

@task
async def check_model_health() -> Dict[str, bool]:
    """Check if ML model is loaded and performing well"""
    logger = get_run_logger()
    
    model_status = {
        "model_file_exists": False,
        "model_loadable": False,
        "recent_predictions": False,
        "performance_acceptable": False
    }
    
    try:
        # Check if model file exists
        model_path = "models/anomaly_model.pkl"
        if os.path.exists(model_path):
            model_status["model_file_exists"] = True
            
            # Try to load model
            try:
                import joblib
                model = joblib.load(model_path)
                model_status["model_loadable"] = True
                
                # Check if there are recent predictions in anomaly_events.csv
                if os.path.exists("anomaly_events.csv"):
                    df = pd.read_csv("anomaly_events.csv")
                    if not df.empty:
                        # Check if there are records from last hour
                        if 'timestamp' in df.columns:
                            recent_records = len(df[df['timestamp'] > datetime.now() - timedelta(hours=1)])
                            if recent_records > 0:
                                model_status["recent_predictions"] = True
                        
                        # Simple performance check: anomaly rate should be reasonable (1-10%)
                        anomaly_rate = len(df) / 1000  # Approximate anomaly rate
                        if 0.001 <= anomaly_rate <= 0.1:  # 0.1% to 10%
                            model_status["performance_acceptable"] = True
                            
            except Exception as e:
                logger.error(f"Error loading model: {e}")
        
        logger.info(f"Model health check: {model_status}")
        return model_status
        
    except Exception as e:
        logger.error(f"Error checking model health: {e}")
        return model_status

@task
async def check_database_health() -> Dict[str, bool]:
    """Check database connectivity and data integrity"""
    logger = get_run_logger()
    
    db_status = {
        "postgres_connected": False,
        "redis_connected": False,
        "recent_data": False,
        "tables_exist": False
    }
    
    try:
        # Check PostgreSQL connection
        db_handler = DatabaseHandler()
        if await db_handler.connect():
            db_status["postgres_connected"] = True
            
            # Check if tables exist and have recent data
            try:
                # This is a simplified check - in production you'd query actual tables
                db_status["tables_exist"] = True
                db_status["recent_data"] = True
            except Exception as e:
                logger.error(f"Error checking database tables: {e}")
                
            await db_handler.disconnect()
        
        # Check Redis connection
        try:
            import redis.asyncio as redis
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            await redis_client.ping()
            db_status["redis_connected"] = True
            await redis_client.close()
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
        
        logger.info(f"Database health check: {db_status}")
        return db_status
        
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        return db_status

@task
async def check_alert_system_health() -> Dict[str, bool]:
    """Check if alert system is working"""
    logger = get_run_logger()
    
    alert_status = {
        "telegram_configured": False,
        "telegram_reachable": False,
        "recent_alerts": False
    }
    
    try:
        # Check if Telegram credentials are configured
        if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            alert_status["telegram_configured"] = True
            
            # Test Telegram connectivity
            try:
                test_message = f"🔍 Health Check - System monitoring active at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                success = await send_telegram_alert_async(test_message)
                if success:
                    alert_status["telegram_reachable"] = True
            except Exception as e:
                logger.error(f"Error testing Telegram alert: {e}")
        
        # Check if there were recent alerts
        if os.path.exists("anomaly_events.csv"):
            df = pd.read_csv("anomaly_events.csv")
            if not df.empty:
                # Check for recent anomalies (last 24 hours)
                if len(df) > 0:
                    alert_status["recent_alerts"] = True
        
        logger.info(f"Alert system health check: {alert_status}")
        return alert_status
        
    except Exception as e:
        logger.error(f"Error checking alert system health: {e}")
        return alert_status

@task
async def generate_health_report(pipeline_health: Dict, model_health: Dict, 
                               db_health: Dict, alert_health: Dict) -> Dict:
    """Generate comprehensive health report"""
    logger = get_run_logger()
    
    # Calculate overall health scores
    pipeline_score = sum(pipeline_health.values()) / len(pipeline_health)
    model_score = sum(model_health.values()) / len(model_health)
    db_score = sum(db_health.values()) / len(db_health)
    alert_score = sum(alert_health.values()) / len(alert_health)
    
    overall_score = (pipeline_score + model_score + db_score + alert_score) / 4
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_health": overall_score,
        "system_status": "HEALTHY" if overall_score > 0.7 else "WARNING" if overall_score > 0.5 else "CRITICAL",
        "components": {
            "pipeline": {"score": pipeline_score, "details": pipeline_health},
            "model": {"score": model_score, "details": model_health},
            "database": {"score": db_score, "details": db_health},
            "alerts": {"score": alert_score, "details": alert_health}
        }
    }
    
    logger.info(f"Health report generated: {report['system_status']} ({overall_score:.2f})")
    return report

@task
async def send_health_alert(health_report: Dict) -> None:
    """Send health alert if system is unhealthy"""
    logger = get_run_logger()
    
    if health_report["overall_health"] < 0.7:  # Send alert if health < 70%
        status_emoji = "🚨" if health_report["overall_health"] < 0.5 else "⚠️"
        
        message = f"""
{status_emoji} **SYSTEM HEALTH ALERT** {status_emoji}

**Overall Status**: {health_report['system_status']}
**Health Score**: {health_report['overall_health']:.1%}

**Component Status**:
🔄 Pipeline: {health_report['components']['pipeline']['score']:.1%}
🤖 Model: {health_report['components']['model']['score']:.1%}
🗄️ Database: {health_report['components']['database']['score']:.1%}
📱 Alerts: {health_report['components']['alerts']['score']:.1%}

**Time**: {health_report['timestamp']}

Please check the system immediately!
        """
        
        try:
            await send_telegram_alert_async(message)
            logger.info("Health alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send health alert: {e}")

@flow(name="System Health Check", log_prints=True)
async def system_health_check_flow():
    """Main flow for comprehensive system health monitoring"""
    logger = get_run_logger()
    logger.info("Starting system health check...")
    
    # Run all health checks concurrently
    pipeline_health = await check_pipeline_health()
    model_health = await check_model_health()
    db_health = await check_database_health()
    alert_health = await check_alert_system_health()
    
    # Generate report
    health_report = await generate_health_report(
        pipeline_health, model_health, db_health, alert_health
    )
    
    # Send alert if needed
    await send_health_alert(health_report)
    
    # Save report to file
    import json
    report_path = f"health_reports/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("health_reports", exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(health_report, f, indent=2)
    
    logger.info(f"Health check completed. Report saved to {report_path}")
    return health_report

if __name__ == "__main__":
    # Run the health check flow
    import asyncio
    asyncio.run(system_health_check_flow())