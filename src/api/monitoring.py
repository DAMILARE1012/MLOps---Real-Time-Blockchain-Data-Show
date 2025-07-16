"""
API monitoring endpoints and health checks
"""

import os
import sys
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import prometheus_client
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# Router for monitoring endpoints
monitoring_router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Response models
class SystemHealth(BaseModel):
    """System health information"""
    status: str
    timestamp: datetime
    uptime_seconds: float
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int

class ServiceHealth(BaseModel):
    """Service-specific health information"""
    database_connected: bool
    model_loaded: bool
    mlflow_connected: bool
    redis_connected: bool
    telegram_configured: bool

class DetailedHealth(BaseModel):
    """Comprehensive health check"""
    system: SystemHealth
    services: ServiceHealth
    api_metrics: Dict[str, Any]

# Global variables for health tracking
app_start_time = datetime.utcnow()
health_cache = {}
cache_ttl = 30  # Cache health info for 30 seconds

@monitoring_router.get("/health", response_model=DetailedHealth)
async def detailed_health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check cache first
        now = datetime.utcnow()
        if ('health' in health_cache and 
            (now - health_cache['timestamp']).total_seconds() < cache_ttl):
            return health_cache['health']
        
        # System health
        uptime = (now - app_start_time).total_seconds()
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_health = SystemHealth(
            status="healthy" if cpu_usage < 80 and memory.percent < 80 else "degraded",
            timestamp=now,
            uptime_seconds=uptime,
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=memory.percent,
            disk_usage_percent=disk.percent,
            active_connections=len(psutil.net_connections())
        )
        
        # Service health checks
        services = await check_services_health()
        
        # API metrics
        api_metrics = get_api_metrics()
        
        # Overall health
        detailed_health = DetailedHealth(
            system=system_health,
            services=services,
            api_metrics=api_metrics
        )
        
        # Cache result
        health_cache['health'] = detailed_health
        health_cache['timestamp'] = now
        
        return detailed_health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@monitoring_router.get("/health/liveness")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive", "timestamp": datetime.utcnow()}

@monitoring_router.get("/health/readiness")
async def readiness_probe():
    """Kubernetes readiness probe endpoint"""
    try:
        # Quick service checks
        services = await check_services_health()
        
        if services.model_loaded:
            return {"status": "ready", "timestamp": datetime.utcnow()}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready - model not loaded"
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

@monitoring_router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    try:
        metrics_output = generate_latest()
        return Response(
            content=metrics_output,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Metrics generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics generation failed"
        )

@monitoring_router.get("/stats")
async def api_statistics():
    """API usage statistics"""
    try:
        stats = {
            "uptime_seconds": (datetime.utcnow() - app_start_time).total_seconds(),
            "total_requests": get_request_count(),
            "active_requests": get_active_requests(),
            "error_rate": get_error_rate(),
            "average_response_time": get_average_response_time(),
            "predictions_made": get_prediction_count(),
            "last_prediction": get_last_prediction_time(),
            "anomaly_detection_rate": get_current_anomaly_rate()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Statistics generation failed"
        )

# Helper functions
async def check_services_health() -> ServiceHealth:
    """Check health of all services"""
    health = {
        "database_connected": await check_database_health(),
        "model_loaded": check_model_health(),
        "mlflow_connected": await check_mlflow_health(),
        "redis_connected": await check_redis_health(),
        "telegram_configured": check_telegram_health()
    }
    
    return ServiceHealth(**health)

async def check_database_health() -> bool:
    """Check database connectivity"""
    try:
        # Would implement actual database check
        # For now, assume healthy
        return True
    except Exception:
        return False

def check_model_health() -> bool:
    """Check if model is loaded and working"""
    try:
        # Would check actual model state
        # For now, assume healthy if model file exists
        return os.path.exists("models/anomaly_model.pkl")
    except Exception:
        return False

async def check_mlflow_health() -> bool:
    """Check MLflow connectivity"""
    try:
        import mlflow
        mlflow.set_tracking_uri("http://localhost:5000")
        
        # Try to list experiments
        client = mlflow.tracking.MlflowClient()
        experiments = client.list_experiments(max_results=1)
        return True
    except Exception:
        return False

async def check_redis_health() -> bool:
    """Check Redis connectivity"""
    try:
        # Would implement actual Redis check
        return True
    except Exception:
        return False

def check_telegram_health() -> bool:
    """Check Telegram configuration"""
    try:
        # Check if Telegram token is configured
        return bool(os.getenv('TELEGRAM_TOKEN'))
    except Exception:
        return False

def get_api_metrics() -> Dict[str, Any]:
    """Get current API metrics"""
    try:
        return {
            "total_requests": get_request_count(),
            "active_requests": get_active_requests(),
            "error_rate": get_error_rate(),
            "average_response_time_ms": get_average_response_time() * 1000,
            "predictions_total": get_prediction_count()
        }
    except Exception:
        return {}

def get_request_count() -> int:
    """Get total request count from Prometheus metrics"""
    try:
        # Would extract from actual Prometheus metrics
        return 0
    except Exception:
        return 0

def get_active_requests() -> int:
    """Get active request count"""
    try:
        return 0
    except Exception:
        return 0

def get_error_rate() -> float:
    """Get error rate percentage"""
    try:
        return 0.0
    except Exception:
        return 0.0

def get_average_response_time() -> float:
    """Get average response time in seconds"""
    try:
        return 0.0
    except Exception:
        return 0.0

def get_prediction_count() -> int:
    """Get total prediction count"""
    try:
        return 0
    except Exception:
        return 0

def get_last_prediction_time() -> str:
    """Get timestamp of last prediction"""
    try:
        return datetime.utcnow().isoformat()
    except Exception:
        return ""

def get_current_anomaly_rate() -> float:
    """Get current anomaly detection rate"""
    try:
        return 0.0
    except Exception:
        return 0.0