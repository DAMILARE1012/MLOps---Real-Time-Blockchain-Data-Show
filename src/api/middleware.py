"""
FastAPI middleware for monitoring, logging, and metrics collection
"""

import time
import logging
from typing import Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'api_active_requests',
    'Active API requests'
)

PREDICTION_COUNT = Counter(
    'predictions_total',
    'Total predictions made',
    ['prediction_type', 'risk_level']
)

ANOMALY_DETECTION_RATE = Gauge(
    'anomaly_detection_rate',
    'Current anomaly detection rate'
)

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        ACTIVE_REQUESTS.inc()
        
        # Extract endpoint info
        method = request.method
        path = request.url.path
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            status_code = 500
            raise
        
        finally:
            # Record metrics
            duration = time.time() - start_time
            ACTIVE_REQUESTS.dec()
            REQUEST_COUNT.labels(
                method=method, 
                endpoint=path, 
                status_code=status_code
            ).inc()
            REQUEST_DURATION.labels(
                method=method, 
                endpoint=path
            ).observe(duration)
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} "
                f"({duration:.3f}s) "
                f"for {request.method} {request.url.path}"
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"({duration:.3f}s) - {str(e)}"
            )
            raise


class SecurityMiddleware(BaseHTTPMiddleware):
    """Basic security headers middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def record_prediction_metrics(prediction_type: str, risk_level: str, anomaly_rate: float = None):
    """Record prediction-specific metrics"""
    PREDICTION_COUNT.labels(
        prediction_type=prediction_type,
        risk_level=risk_level
    ).inc()
    
    if anomaly_rate is not None:
        ANOMALY_DETECTION_RATE.set(anomaly_rate)