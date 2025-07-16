"""
FastAPI application for blockchain anomaly detection
Provides REST API endpoints for real-time and batch anomaly detection
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import joblib
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, validator
import uvicorn

# Import custom middleware and monitoring
from api.middleware import MetricsMiddleware, LoggingMiddleware, SecurityMiddleware
from api.monitoring import monitoring_router

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import our modules
try:
    from anomaly_detection.model_registry import ModelRegistry
    from data_pipeline.database_handler import DatabaseHandler
    from alerting.telegram_alert import send_telegram_alert_async
except ImportError as e:
    logging.warning(f"Some modules not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Blockchain Anomaly Detection API",
    description="Real-time anomaly detection for blockchain transactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add custom middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include monitoring router
app.include_router(monitoring_router)

# Global model storage
model_cache = {}
model_registry = None

# Pydantic models for API
class Transaction(BaseModel):
    """Single blockchain transaction for anomaly detection"""
    total_value: float = Field(..., description="Total transaction value in satoshis", gt=0)
    fee: float = Field(..., description="Transaction fee in satoshis", ge=0)
    input_count: int = Field(..., description="Number of inputs", gt=0)
    output_count: int = Field(..., description="Number of outputs", gt=0)
    timestamp: Optional[datetime] = Field(None, description="Transaction timestamp")
    
    @validator('total_value', 'fee')
    def validate_positive_values(cls, v):
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v

class BatchTransactions(BaseModel):
    """Batch of transactions for analysis"""
    transactions: List[Transaction] = Field(..., description="List of transactions to analyze")
    
    @validator('transactions')
    def validate_batch_size(cls, v):
        if len(v) == 0:
            raise ValueError('Batch must contain at least one transaction')
        if len(v) > 1000:
            raise ValueError('Batch size cannot exceed 1000 transactions')
        return v

class AnomalyPrediction(BaseModel):
    """Anomaly detection result for a single transaction"""
    is_anomaly: bool = Field(..., description="Whether transaction is anomalous")
    anomaly_score: float = Field(..., description="Anomaly score (lower = more anomalous)")
    confidence: float = Field(..., description="Prediction confidence (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")

class BatchPredictionResponse(BaseModel):
    """Response for batch predictions"""
    predictions: List[AnomalyPrediction]
    summary: Dict[str, Any]
    processing_time_ms: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    model_loaded: bool
    model_version: Optional[str]
    uptime_seconds: float
    database_connected: bool

# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global model_cache, model_registry
    
    logger.info("Starting Blockchain Anomaly Detection API...")
    
    try:
        # Initialize model registry
        model_registry = ModelRegistry()
        
        # Load production model
        model = model_registry.get_production_model()
        if model:
            model_cache['production'] = model
            logger.info("Production model loaded successfully")
        else:
            # Fallback to local model
            local_model_path = "models/anomaly_model.pkl"
            if os.path.exists(local_model_path):
                model_cache['production'] = joblib.load(local_model_path)
                logger.info("Local model loaded as fallback")
            else:
                logger.warning("No model available - API will have limited functionality")
        
        # Load scaler if available
        scaler_path = "models/scaler.pkl"
        if os.path.exists(scaler_path):
            model_cache['scaler'] = joblib.load(scaler_path)
            logger.info("Feature scaler loaded")
        
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Blockchain Anomaly Detection API...")

# Dependency functions
def get_model():
    """Get the current production model"""
    if 'production' not in model_cache:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not available"
        )
    return model_cache['production']

def get_scaler():
    """Get the feature scaler"""
    return model_cache.get('scaler', None)

# Utility functions
def prepare_features(transaction: Transaction) -> np.ndarray:
    """Convert transaction to feature array"""
    features = np.array([[
        transaction.total_value,
        transaction.fee,
        transaction.input_count,
        transaction.output_count
    ]])
    
    # Apply scaling if available
    scaler = get_scaler()
    if scaler:
        features = scaler.transform(features)
    
    return features

def calculate_risk_level(score: float) -> str:
    """Calculate risk level based on anomaly score"""
    if score > 0.1:
        return "low"
    elif score > 0.0:
        return "medium"
    elif score > -0.3:
        return "high"
    else:
        return "critical"

def create_prediction(score: float, prediction: int) -> AnomalyPrediction:
    """Create prediction response from model output"""
    is_anomaly = prediction == -1
    confidence = min(abs(score) * 2, 1.0)  # Normalize confidence
    risk_level = calculate_risk_level(score)
    
    return AnomalyPrediction(
        is_anomaly=is_anomaly,
        anomaly_score=float(score),
        confidence=confidence,
        risk_level=risk_level
    )

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """API root endpoint"""
    return {
        "message": "Blockchain Anomaly Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check model availability
        model_loaded = 'production' in model_cache
        model_version = None
        
        if model_registry:
            try:
                versions = model_registry.get_model_versions()
                prod_versions = [v for v in versions if v['stage'] == 'Production']
                if prod_versions:
                    model_version = prod_versions[0]['version']
            except Exception:
                pass
        
        # Check database connectivity
        database_connected = False
        try:
            # This would check actual database connection
            database_connected = True
        except Exception:
            pass
        
        return HealthResponse(
            status="healthy" if model_loaded else "degraded",
            timestamp=datetime.utcnow(),
            model_loaded=model_loaded,
            model_version=model_version,
            uptime_seconds=0.0,  # Would track actual uptime
            database_connected=database_connected
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@app.post("/predict/anomaly", response_model=AnomalyPrediction)
async def predict_anomaly(
    transaction: Transaction,
    model=Depends(get_model)
):
    """Predict if a single transaction is anomalous"""
    try:
        # Prepare features
        features = prepare_features(transaction)
        
        # Make prediction
        prediction = model.predict(features)[0]
        score = model.decision_function(features)[0]
        
        # Create response
        result = create_prediction(score, prediction)
        
        # Log high-risk transactions
        if result.risk_level in ["high", "critical"]:
            logger.warning(
                f"High-risk transaction detected: "
                f"value={transaction.total_value}, "
                f"score={score:.3f}, "
                f"risk={result.risk_level}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed"
        )

@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(
    batch: BatchTransactions,
    background_tasks: BackgroundTasks,
    model=Depends(get_model)
):
    """Predict anomalies for a batch of transactions"""
    start_time = datetime.utcnow()
    
    try:
        predictions = []
        anomaly_count = 0
        high_risk_count = 0
        
        # Process each transaction
        for transaction in batch.transactions:
            features = prepare_features(transaction)
            prediction = model.predict(features)[0]
            score = model.decision_function(features)[0]
            
            result = create_prediction(score, prediction)
            predictions.append(result)
            
            if result.is_anomaly:
                anomaly_count += 1
            if result.risk_level in ["high", "critical"]:
                high_risk_count += 1
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create summary
        summary = {
            "total_transactions": len(batch.transactions),
            "anomalies_detected": anomaly_count,
            "anomaly_rate": anomaly_count / len(batch.transactions),
            "high_risk_transactions": high_risk_count,
            "average_score": float(np.mean([p.anomaly_score for p in predictions])),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Send alert for high anomaly rate
        if summary["anomaly_rate"] > 0.1:  # >10% anomaly rate
            background_tasks.add_task(
                send_batch_alert,
                summary["anomaly_rate"],
                summary["total_transactions"]
            )
        
        return BatchPredictionResponse(
            predictions=predictions,
            summary=summary,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch prediction failed"
        )

@app.get("/model/info")
async def get_model_info():
    """Get information about the current model"""
    try:
        info = {
            "model_loaded": 'production' in model_cache,
            "model_type": "IsolationForest",
            "feature_count": 4,
            "features": ["total_value", "fee", "input_count", "output_count"]
        }
        
        if model_registry:
            try:
                versions = model_registry.get_model_versions()
                if versions:
                    info["available_versions"] = len(versions)
                    prod_versions = [v for v in versions if v['stage'] == 'Production']
                    if prod_versions:
                        info["production_version"] = prod_versions[0]['version']
                        info["model_stage"] = "Production"
            except Exception as e:
                logger.warning(f"Could not get model registry info: {e}")
        
        return info
        
    except Exception as e:
        logger.error(f"Model info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve model information"
        )

@app.get("/model/performance")
async def get_model_performance():
    """Get model performance metrics"""
    try:
        if not model_registry:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model registry not available"
            )
        
        # Get performance history
        performance_df = model_registry.get_model_performance_history()
        
        if performance_df.empty:
            return {"message": "No performance data available"}
        
        # Get latest performance metrics
        latest = performance_df.iloc[0]
        
        return {
            "latest_version": latest.get("version"),
            "anomaly_rate": latest.get("anomaly_rate"),
            "mean_score": latest.get("mean_anomaly_score"),
            "training_samples": latest.get("n_samples"),
            "last_updated": latest.get("creation_time", datetime.utcnow()).isoformat(),
            "total_versions": len(performance_df)
        }
        
    except Exception as e:
        logger.error(f"Performance info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve performance information"
        )

@app.post("/model/reload")
async def reload_model():
    """Reload the production model"""
    try:
        global model_cache
        
        if not model_registry:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model registry not available"
            )
        
        # Load latest production model
        model = model_registry.get_production_model()
        if model:
            model_cache['production'] = model
            logger.info("Production model reloaded successfully")
            return {"message": "Model reloaded successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No production model available"
            )
        
    except Exception as e:
        logger.error(f"Model reload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model reload failed"
        )

# Background tasks
async def send_batch_alert(anomaly_rate: float, total_transactions: int):
    """Send alert for high anomaly rate in batch"""
    try:
        message = f"""
🚨 **HIGH ANOMALY RATE DETECTED** 🚨

📊 **Batch Analysis Alert**:
  • Anomaly Rate: {anomaly_rate:.1%}
  • Total Transactions: {total_transactions}
  • Threshold Exceeded: >10%

⚠️ This indicates potential suspicious activity in the analyzed transaction batch.
🕒 **Timestamp**: {datetime.utcnow().isoformat()}
        """
        
        await send_telegram_alert_async(message)
        logger.info(f"Batch alert sent for {anomaly_rate:.1%} anomaly rate")
        
    except Exception as e:
        logger.error(f"Failed to send batch alert: {e}")

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )