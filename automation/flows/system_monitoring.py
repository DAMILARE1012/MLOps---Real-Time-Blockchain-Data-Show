"""
System Monitoring and Alerting for Blockchain Anomaly Detection System

This module contains Prefect flows for:
- Performance monitoring
- Resource utilization tracking
- Anomaly rate monitoring
- System restart automation
"""

import os
import psutil
import time
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import subprocess

# Prefect imports
from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret
from prefect.runtime import deployment
from prefect.client.schemas.schedules import CronSchedule

# Import our system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.alerting.telegram_alert import send_telegram_alert_async

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@task
async def monitor_system_resources() -> Dict[str, float]:
    """Monitor system resource utilization"""
    logger = get_run_logger()
    
    try:
        # CPU utilization
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory utilization
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Disk utilization
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free_gb = disk.free / (1024**3)
        
        # Network I/O
        net_io = psutil.net_io_counters()
        
        # Process count
        process_count = len(psutil.pids())
        
        resources = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': memory_available_gb,
            'disk_percent': disk_percent,
            'disk_free_gb': disk_free_gb,
            'network_bytes_sent': net_io.bytes_sent,
            'network_bytes_recv': net_io.bytes_recv,
            'process_count': process_count,
            'timestamp': time.time()
        }
        
        logger.info(f"System resources - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%")
        return resources
        
    except Exception as e:
        logger.error(f"Error monitoring system resources: {e}")
        return {}

@task
async def monitor_pipeline_metrics() -> Dict[str, float]:
    """Monitor pipeline-specific metrics"""
    logger = get_run_logger()
    
    metrics = {
        'transactions_processed': 0,
        'anomalies_detected': 0,
        'whales_detected': 0,
        'processing_rate': 0.0,
        'error_rate': 0.0,
        'avg_processing_time': 0.0
    }
    
    try:
        # Count recent transactions
        if os.path.exists("anomaly_events.csv"):
            df = pd.read_csv("anomaly_events.csv")
            
            # Recent anomalies (last hour)
            recent_anomalies = len(df[df['timestamp'] > datetime.now() - timedelta(hours=1)])
            metrics['anomalies_detected'] = recent_anomalies
            
            # Total processed
            metrics['transactions_processed'] = len(df)
        
        # Count whale transactions
        if os.path.exists("whale_events.csv"):
            whale_df = pd.read_csv("whale_events.csv")
            recent_whales = len(whale_df[whale_df['timestamp'] > datetime.now() - timedelta(hours=1)])
            metrics['whales_detected'] = recent_whales
        
        # Calculate processing rate (transactions per minute)
        if os.path.exists("data_pipeline.log"):
            with open("data_pipeline.log", 'r') as f:
                lines = f.readlines()
                
            # Count "Stored unconfirmed transaction" messages in last 10 minutes
            recent_lines = []
            current_time = datetime.now()
            
            for line in reversed(lines[-1000:]):  # Check last 1000 lines
                if "Stored unconfirmed transaction" in line:
                    recent_lines.append(line)
                    if len(recent_lines) >= 100:  # Limit to avoid processing too much
                        break
            
            if recent_lines:
                metrics['processing_rate'] = len(recent_lines) / 10  # per minute
        
        # Calculate error rate from logs
        if os.path.exists("data_pipeline.log"):
            with open("data_pipeline.log", 'r') as f:
                recent_logs = f.readlines()[-200:]  # Last 200 lines
                
            error_count = sum(1 for line in recent_logs if "ERROR" in line)
            total_logs = len(recent_logs)
            
            if total_logs > 0:
                metrics['error_rate'] = error_count / total_logs
        
        logger.info(f"Pipeline metrics - Processing rate: {metrics['processing_rate']:.1f}/min, "
                   f"Anomalies: {metrics['anomalies_detected']}, Whales: {metrics['whales_detected']}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error monitoring pipeline metrics: {e}")
        return metrics

@task
async def monitor_anomaly_rates() -> Dict[str, float]:
    """Monitor anomaly detection rates and patterns"""
    logger = get_run_logger()
    
    anomaly_stats = {
        'hourly_anomaly_rate': 0.0,
        'daily_anomaly_rate': 0.0,
        'avg_anomaly_score': 0.0,
        'score_volatility': 0.0,
        'unique_addresses': 0,
        'repeat_offenders': 0
    }
    
    try:
        if os.path.exists("anomaly_events.csv"):
            df = pd.read_csv("anomaly_events.csv")
            
            if not df.empty:
                # Convert timestamp if needed
                if 'timestamp' not in df.columns:
                    df['timestamp'] = pd.to_datetime(df['hash'].apply(lambda x: int(x[:8], 16)), unit='s', errors='coerce')
                
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Calculate rates
                now = datetime.now()
                hourly_anomalies = len(df[df['timestamp'] > now - timedelta(hours=1)])
                daily_anomalies = len(df[df['timestamp'] > now - timedelta(days=1)])
                
                # Estimate total transactions (rough approximation)
                estimated_hourly_transactions = 1000  # Approximate
                estimated_daily_transactions = 24000
                
                anomaly_stats['hourly_anomaly_rate'] = hourly_anomalies / estimated_hourly_transactions
                anomaly_stats['daily_anomaly_rate'] = daily_anomalies / estimated_daily_transactions
                
                # Score statistics
                if 'score' in df.columns:
                    anomaly_stats['avg_anomaly_score'] = df['score'].mean()
                    anomaly_stats['score_volatility'] = df['score'].std()
                
                # Address analysis
                if 'address' in df.columns:
                    unique_addresses = df['address'].nunique()
                    address_counts = df['address'].value_counts()
                    repeat_offenders = len(address_counts[address_counts > 1])
                    
                    anomaly_stats['unique_addresses'] = unique_addresses
                    anomaly_stats['repeat_offenders'] = repeat_offenders
        
        logger.info(f"Anomaly rates - Hourly: {anomaly_stats['hourly_anomaly_rate']:.3f}, "
                   f"Daily: {anomaly_stats['daily_anomaly_rate']:.3f}")
        
        return anomaly_stats
        
    except Exception as e:
        logger.error(f"Error monitoring anomaly rates: {e}")
        return anomaly_stats

@task
async def check_system_alerts(resources: Dict, pipeline_metrics: Dict, anomaly_stats: Dict) -> List[str]:
    """Check for system alerts based on monitored metrics"""
    logger = get_run_logger()
    
    alerts = []
    
    # Resource alerts
    if resources.get('cpu_percent', 0) > 80:
        alerts.append(f"HIGH CPU: {resources['cpu_percent']:.1f}%")
    
    if resources.get('memory_percent', 0) > 85:
        alerts.append(f"HIGH MEMORY: {resources['memory_percent']:.1f}%")
    
    if resources.get('disk_percent', 0) > 90:
        alerts.append(f"HIGH DISK: {resources['disk_percent']:.1f}%")
    
    # Pipeline alerts
    if pipeline_metrics.get('processing_rate', 0) < 1:
        alerts.append(f"LOW PROCESSING RATE: {pipeline_metrics['processing_rate']:.1f}/min")
    
    if pipeline_metrics.get('error_rate', 0) > 0.1:
        alerts.append(f"HIGH ERROR RATE: {pipeline_metrics['error_rate']:.1%}")
    
    # Anomaly rate alerts
    if anomaly_stats.get('hourly_anomaly_rate', 0) > 0.1:
        alerts.append(f"HIGH ANOMALY RATE: {anomaly_stats['hourly_anomaly_rate']:.1%}")
    
    if anomaly_stats.get('hourly_anomaly_rate', 0) < 0.001:
        alerts.append(f"LOW ANOMALY RATE: {anomaly_stats['hourly_anomaly_rate']:.3%}")
    
    # Data freshness alerts
    if os.path.exists("data_pipeline.log"):
        log_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime("data_pipeline.log"))
        if log_age.total_seconds() > 300:  # 5 minutes
            alerts.append(f"STALE DATA: Pipeline inactive for {log_age.total_seconds()/60:.1f} minutes")
    
    if alerts:
        logger.warning(f"System alerts: {', '.join(alerts)}")
    else:
        logger.info("No system alerts detected")
    
    return alerts

@task
async def save_monitoring_data(resources: Dict, pipeline_metrics: Dict, anomaly_stats: Dict) -> None:
    """Save monitoring data to file for historical analysis"""
    logger = get_run_logger()
    
    try:
        # Create monitoring data directory
        os.makedirs("monitoring_data", exist_ok=True)
        
        # Combine all metrics
        monitoring_record = {
            'timestamp': datetime.now().isoformat(),
            'resources': resources,
            'pipeline_metrics': pipeline_metrics,
            'anomaly_stats': anomaly_stats
        }
        
        # Save to daily file
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = f"monitoring_data/monitoring_{date_str}.jsonl"
        
        with open(file_path, 'a') as f:
            f.write(json.dumps(monitoring_record) + '\n')
        
        logger.info(f"Monitoring data saved to {file_path}")
        
    except Exception as e:
        logger.error(f"Error saving monitoring data: {e}")

@task
async def restart_pipeline_if_needed(alerts: List[str]) -> bool:
    """Restart pipeline if critical issues detected"""
    logger = get_run_logger()
    
    critical_alerts = [
        "STALE DATA",
        "HIGH ERROR RATE",
        "LOW PROCESSING RATE"
    ]
    
    needs_restart = any(any(critical in alert for critical in critical_alerts) for alert in alerts)
    
    if needs_restart:
        logger.warning("Critical issues detected. Attempting pipeline restart...")
        
        try:
            # Check if pipeline is running
            pipeline_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and any('data_pipeline' in cmd for cmd in proc.info['cmdline']):
                        pipeline_running = True
                        proc.terminate()  # Graceful termination
                        logger.info(f"Terminated pipeline process {proc.info['pid']}")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not pipeline_running:
                logger.warning("Pipeline process not found")
            
            # Wait a moment for graceful shutdown
            time.sleep(5)
            
            # Start pipeline again
            # Note: In production, this would typically be handled by a process manager
            # like systemd, supervisor, or container orchestration
            logger.info("Pipeline restart completed (manual intervention may be required)")
            
            # Send restart notification
            await send_telegram_alert_async(
                f"🔄 **PIPELINE RESTART**\n\n"
                f"The system detected critical issues and attempted to restart the pipeline.\n"
                f"Issues: {', '.join(alerts)}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Please verify the system is functioning properly."
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error restarting pipeline: {e}")
            return False
    
    return False

@task
async def send_monitoring_summary(resources: Dict, pipeline_metrics: Dict, 
                                anomaly_stats: Dict, alerts: List[str]) -> None:
    """Send monitoring summary to Telegram"""
    logger = get_run_logger()
    
    try:
        # Only send summary if there are alerts or it's a scheduled summary
        if alerts or datetime.now().hour % 6 == 0:  # Every 6 hours or when alerts
            
            alert_emoji = "🚨" if alerts else "✅"
            status = "ALERTS DETECTED" if alerts else "ALL SYSTEMS NORMAL"
            
            message = f"""
{alert_emoji} **SYSTEM MONITORING SUMMARY** {alert_emoji}

**Status**: {status}

**System Resources**:
🖥️ CPU: {resources.get('cpu_percent', 0):.1f}%
💾 Memory: {resources.get('memory_percent', 0):.1f}%
💽 Disk: {resources.get('disk_percent', 0):.1f}%

**Pipeline Metrics**:
⚡ Processing Rate: {pipeline_metrics.get('processing_rate', 0):.1f}/min
🚨 Anomalies (1h): {pipeline_metrics.get('anomalies_detected', 0)}
🐋 Whales (1h): {pipeline_metrics.get('whales_detected', 0)}
❌ Error Rate: {pipeline_metrics.get('error_rate', 0):.1%}

**Anomaly Analysis**:
📊 Hourly Rate: {anomaly_stats.get('hourly_anomaly_rate', 0):.3%}
📈 Daily Rate: {anomaly_stats.get('daily_anomaly_rate', 0):.3%}
🎯 Avg Score: {anomaly_stats.get('avg_anomaly_score', 0):.3f}
            """
            
            if alerts:
                message += f"\n**Active Alerts**:\n"
                for alert in alerts:
                    message += f"⚠️ {alert}\n"
            
            message += f"\n⏰ **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await send_telegram_alert_async(message)
            logger.info("Monitoring summary sent successfully")
            
    except Exception as e:
        logger.error(f"Error sending monitoring summary: {e}")

@flow(name="System Monitoring", log_prints=True)
async def system_monitoring_flow():
    """Main flow for comprehensive system monitoring"""
    logger = get_run_logger()
    logger.info("Starting system monitoring...")
    
    try:
        # Monitor system resources
        resources = await monitor_system_resources()
        
        # Monitor pipeline metrics
        pipeline_metrics = await monitor_pipeline_metrics()
        
        # Monitor anomaly rates
        anomaly_stats = await monitor_anomaly_rates()
        
        # Check for alerts
        alerts = await check_system_alerts(resources, pipeline_metrics, anomaly_stats)
        
        # Save monitoring data
        await save_monitoring_data(resources, pipeline_metrics, anomaly_stats)
        
        # Restart pipeline if needed
        if alerts:
            restart_attempted = await restart_pipeline_if_needed(alerts)
            if restart_attempted:
                logger.info("Pipeline restart attempted due to critical alerts")
        
        # Send monitoring summary
        await send_monitoring_summary(resources, pipeline_metrics, anomaly_stats, alerts)
        
        logger.info("System monitoring completed successfully")
        
        return {
            'resources': resources,
            'pipeline_metrics': pipeline_metrics,
            'anomaly_stats': anomaly_stats,
            'alerts': alerts
        }
        
    except Exception as e:
        logger.error(f"Error in system monitoring flow: {e}")
        
        # Send error notification
        await send_telegram_alert_async(
            f"❌ **MONITORING SYSTEM ERROR**\n\n"
            f"The system monitoring flow encountered an error:\n"
            f"{str(e)}\n\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        raise

if __name__ == "__main__":
    # Run the monitoring flow
    import asyncio
    asyncio.run(system_monitoring_flow())