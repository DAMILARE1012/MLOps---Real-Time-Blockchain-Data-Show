"""
Automated Model Retraining Pipeline for Blockchain Anomaly Detection

This module contains Prefect flows for:
- Data drift detection
- Model performance monitoring
- Automated retraining
- Model validation and deployment
"""

import os
import shutil
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
import joblib

# ML imports
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# MLflow imports
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

# Prefect imports
from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret
from prefect.runtime import deployment
from prefect.client.schemas.schedules import CronSchedule

# Import our system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.alerting.telegram_alert import send_telegram_alert_async
from src.anomaly_detection.feature_extraction import extract_features_from_transaction
from src.anomaly_detection.model_registry import ModelRegistry
# from src.anomaly_detection.model_performance import ModelPerformanceMonitor

# MLflow configuration
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("blockchain_model_retraining")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@task
async def collect_training_data() -> Tuple[pd.DataFrame, int]:
    """Collect and prepare training data from recent transactions"""
    logger = get_run_logger()
    
    try:
        # Load recent anomaly events
        anomaly_df = pd.DataFrame()
        if os.path.exists("anomaly_events.csv"):
            anomaly_df = pd.read_csv("anomaly_events.csv")
            logger.info(f"Loaded {len(anomaly_df)} anomaly records")
        
        # Load recent whale events
        whale_df = pd.DataFrame()
        if os.path.exists("whale_events.csv"):
            whale_df = pd.read_csv("whale_events.csv")
            logger.info(f"Loaded {len(whale_df)} whale records")
        
        # Create training dataset
        training_data = []
        
        # Process anomaly events (labeled as anomalies)
        for _, row in anomaly_df.iterrows():
            features = {
                'total_value': row.get('total_value', 0),
                'fee': row.get('fee', 0),
                'input_count': row.get('input_count', 0),
                'output_count': row.get('output_count', 0),
                'is_anomaly': 1  # Label as anomaly
            }
            training_data.append(features)
        
        # Process whale events (some may be legitimate large transactions)
        for _, row in whale_df.iterrows():
            features = {
                'total_value': row.get('total_value_btc', 0) * 1e8,  # Convert to satoshis
                'fee': row.get('fee', 0),
                'input_count': row.get('input_count', 0),
                'output_count': row.get('output_count', 0),
                'is_anomaly': 0  # Most whales are legitimate
            }
            training_data.append(features)
        
        # Create synthetic normal transactions for better training
        np.random.seed(42)
        normal_count = len(training_data) * 10  # 10x normal transactions
        
        for _ in range(normal_count):
            features = {
                'total_value': np.random.exponential(50000),  # Typical transaction values
                'fee': np.random.exponential(1000),
                'input_count': np.random.poisson(2) + 1,
                'output_count': np.random.poisson(2) + 1,
                'is_anomaly': 0
            }
            training_data.append(features)
        
        df = pd.DataFrame(training_data)
        total_samples = len(df)
        
        logger.info(f"Created training dataset with {total_samples} samples")
        logger.info(f"Anomaly ratio: {df['is_anomaly'].mean():.3f}")
        
        return df, total_samples
        
    except Exception as e:
        logger.error(f"Error collecting training data: {e}")
        raise

@task
async def detect_data_drift(current_data: pd.DataFrame) -> Dict[str, float]:
    """Detect data drift by comparing current data with historical data"""
    logger = get_run_logger()
    
    drift_metrics = {
        'total_value_drift': 0.0,
        'fee_drift': 0.0,
        'input_count_drift': 0.0,
        'output_count_drift': 0.0,
        'overall_drift': 0.0
    }
    
    try:
        # Load historical data for comparison
        historical_file = "models/historical_features.csv"
        if os.path.exists(historical_file):
            historical_data = pd.read_csv(historical_file)
            
            # Calculate drift using statistical distance measures
            features = ['total_value', 'fee', 'input_count', 'output_count']
            
            for feature in features:
                if feature in current_data.columns and feature in historical_data.columns:
                    # Use Kolmogorov-Smirnov test for drift detection
                    from scipy.stats import ks_2samp
                    
                    current_feature = current_data[feature].dropna()
                    historical_feature = historical_data[feature].dropna()
                    
                    if len(current_feature) > 0 and len(historical_feature) > 0:
                        statistic, p_value = ks_2samp(current_feature, historical_feature)
                        drift_metrics[f'{feature}_drift'] = statistic
                        
                        logger.info(f"{feature} drift: {statistic:.3f} (p-value: {p_value:.3f})")
            
            # Calculate overall drift
            drift_metrics['overall_drift'] = np.mean([
                drift_metrics['total_value_drift'],
                drift_metrics['fee_drift'],
                drift_metrics['input_count_drift'],
                drift_metrics['output_count_drift']
            ])
            
            logger.info(f"Overall data drift: {drift_metrics['overall_drift']:.3f}")
        
        return drift_metrics
        
    except Exception as e:
        logger.error(f"Error detecting data drift: {e}")
        return drift_metrics

@task
async def evaluate_model_performance() -> Dict[str, float]:
    """Evaluate current model performance"""
    logger = get_run_logger()
    
    performance_metrics = {
        'accuracy': 0.0,
        'precision': 0.0,
        'recall': 0.0,
        'f1_score': 0.0,
        'anomaly_detection_rate': 0.0
    }
    
    try:
        # Load current model
        model_path = "models/anomaly_model.pkl"
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            
            # Load recent data for evaluation
            if os.path.exists("anomaly_events.csv"):
                df = pd.read_csv("anomaly_events.csv")
                
                if len(df) > 10:  # Need sufficient data
                    # Evaluate on recent anomalies
                    recent_anomalies = df.tail(100)  # Last 100 anomalies
                    
                    # Calculate detection rate
                    detection_rate = len(recent_anomalies) / 1000  # Approximate
                    performance_metrics['anomaly_detection_rate'] = detection_rate
                    
                    # Calculate score distribution
                    scores = recent_anomalies['score'].values
                    performance_metrics['accuracy'] = np.mean(scores < -0.05)  # Threshold-based
                    
                    logger.info(f"Model performance metrics: {performance_metrics}")
        
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Error evaluating model performance: {e}")
        return performance_metrics

@task
async def should_retrain_model(drift_metrics: Dict[str, float], 
                             performance_metrics: Dict[str, float]) -> bool:
    """Determine if model should be retrained based on drift and performance"""
    logger = get_run_logger()
    
    # Retraining criteria
    high_drift_threshold = 0.3
    low_performance_threshold = 0.7
    
    should_retrain = False
    reasons = []
    
    # Check for significant data drift
    if drift_metrics['overall_drift'] > high_drift_threshold:
        should_retrain = True
        reasons.append(f"High data drift detected ({drift_metrics['overall_drift']:.3f})")
    
    # Check for poor performance
    if performance_metrics['accuracy'] < low_performance_threshold:
        should_retrain = True
        reasons.append(f"Poor model performance ({performance_metrics['accuracy']:.3f})")
    
    # Check for abnormal anomaly detection rate
    if performance_metrics['anomaly_detection_rate'] < 0.001 or performance_metrics['anomaly_detection_rate'] > 0.1:
        should_retrain = True
        reasons.append(f"Abnormal detection rate ({performance_metrics['anomaly_detection_rate']:.3f})")
    
    # Time-based retraining (weekly)
    model_path = "models/anomaly_model.pkl"
    if os.path.exists(model_path):
        model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
        if model_age.days > 7:
            should_retrain = True
            reasons.append(f"Model is {model_age.days} days old")
    
    if should_retrain:
        logger.info(f"Retraining decision: YES. Reasons: {', '.join(reasons)}")
    else:
        logger.info("Retraining decision: NO. Model is performing well.")
    
    return should_retrain

@task
async def train_new_model(training_data: pd.DataFrame) -> Dict[str, any]:
    """Train a new anomaly detection model with MLflow tracking"""
    logger = get_run_logger()
    
    try:
        with mlflow.start_run(run_name="retraining_experiment") as run:
            # Prepare features
            feature_columns = ['total_value', 'fee', 'input_count', 'output_count']
            X = training_data[feature_columns].values
            y = training_data['is_anomaly'].values
            
            # Log data information
            mlflow.log_param("feature_columns", feature_columns)
            mlflow.log_param("total_samples", len(training_data))
            mlflow.log_param("anomaly_ratio", y.mean())
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            mlflow.log_param("train_samples", len(X_train))
            mlflow.log_param("test_samples", len(X_test))
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Isolation Forest model
            contamination = 0.1
            n_estimators = 100
            
            model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=n_estimators,
                max_samples='auto'
            )
            
            # Log model parameters
            mlflow.log_param("algorithm", "IsolationForest")
            mlflow.log_param("contamination", contamination)
            mlflow.log_param("n_estimators", n_estimators)
            mlflow.log_param("max_samples", "auto")
            
            # Fit only on normal transactions for unsupervised learning
            normal_data = X_train_scaled[y_train == 0]
            model.fit(normal_data)
            
            mlflow.log_param("normal_training_samples", len(normal_data))
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            y_pred_binary = (y_pred == -1).astype(int)  # -1 means anomaly
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            accuracy = accuracy_score(y_test, y_pred_binary)
            precision = precision_score(y_test, y_pred_binary, zero_division=0)
            recall = recall_score(y_test, y_pred_binary, zero_division=0)
            f1 = f1_score(y_test, y_pred_binary, zero_division=0)
            
            # Log metrics
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("recall", recall)
            mlflow.log_metric("f1_score", f1)
            
            # Log additional metrics
            anomaly_scores = model.decision_function(X_test_scaled)
            mlflow.log_metric("mean_anomaly_score", np.mean(anomaly_scores))
            mlflow.log_metric("std_anomaly_score", np.std(anomaly_scores))
            
            # Log model
            mlflow.sklearn.log_model(
                model, 
                "retraining_model",
                registered_model_name="blockchain_anomaly_detector"
            )
            
            # Log scaler as artifact
            scaler_path = "temp_scaler.pkl"
            joblib.dump(scaler, scaler_path)
            mlflow.log_artifact(scaler_path, "preprocessing")
            os.remove(scaler_path)  # Clean up
            
            model_info = {
                'model': model,
                'scaler': scaler,
                'feature_columns': feature_columns,
                'training_samples': len(X_train),
                'performance': {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'test_samples': len(X_test)
                },
                'timestamp': datetime.now().isoformat(),
                'mlflow_run_id': run.info.run_id
            }
            
            logger.info(f"New model trained successfully:")
            logger.info(f"  - Training samples: {len(X_train)}")
            logger.info(f"  - Accuracy: {accuracy:.3f}")
            logger.info(f"  - Precision: {precision:.3f}")
            logger.info(f"  - Recall: {recall:.3f}")
            logger.info(f"  - F1 Score: {f1:.3f}")
            logger.info(f"  - MLflow Run ID: {run.info.run_id}")
            
            return model_info
        
    except Exception as e:
        logger.error(f"Error training new model: {e}")
        raise

@task
async def validate_new_model(model_info: Dict[str, any]) -> bool:
    """Validate new model before deployment"""
    logger = get_run_logger()
    
    try:
        performance = model_info['performance']
        
        # Validation criteria
        min_accuracy = 0.7
        min_precision = 0.5
        min_recall = 0.3
        min_f1 = 0.4
        
        validation_passed = (
            performance['accuracy'] >= min_accuracy and
            performance['precision'] >= min_precision and
            performance['recall'] >= min_recall and
            performance['f1_score'] >= min_f1
        )
        
        if validation_passed:
            logger.info("New model validation: PASSED")
        else:
            logger.warning("New model validation: FAILED")
            logger.warning(f"  - Accuracy: {performance['accuracy']:.3f} (min: {min_accuracy})")
            logger.warning(f"  - Precision: {performance['precision']:.3f} (min: {min_precision})")
            logger.warning(f"  - Recall: {performance['recall']:.3f} (min: {min_recall})")
            logger.warning(f"  - F1 Score: {performance['f1_score']:.3f} (min: {min_f1})")
        
        return validation_passed
        
    except Exception as e:
        logger.error(f"Error validating new model: {e}")
        return False

@task
async def deploy_new_model(model_info: Dict[str, any]) -> bool:
    """Deploy new model to production with MLflow model registry"""
    logger = get_run_logger()
    
    try:
        # Initialize model registry
        registry = ModelRegistry()
        
        # Register the new model version
        run_id = model_info['mlflow_run_id']
        version = registry.register_model(run_id, "retraining_model")
        
        logger.info(f"Registered new model version: {version}")
        
        # Promote to staging first
        registry.promote_model(version, "Staging")
        logger.info(f"Promoted model version {version} to Staging")
        
        # Create backup of current model
        current_model_path = "models/anomaly_model.pkl"
        if os.path.exists(current_model_path):
            backup_path = f"models/anomaly_model_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            shutil.copy2(current_model_path, backup_path)
            logger.info(f"Current model backed up to {backup_path}")
        
        # Save new model locally
        os.makedirs("models", exist_ok=True)
        joblib.dump(model_info['model'], current_model_path)
        
        # Save scaler
        scaler_path = "models/scaler.pkl"
        joblib.dump(model_info['scaler'], scaler_path)
        
        # Save model metadata with MLflow info
        metadata = {
            'feature_columns': model_info['feature_columns'],
            'training_samples': model_info['training_samples'],
            'performance': model_info['performance'],
            'timestamp': model_info['timestamp'],
            'mlflow_run_id': run_id,
            'model_version': version
        }
        
        metadata_path = "models/model_metadata.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Promote to production after successful deployment
        registry.promote_model(version, "Production")
        logger.info(f"Promoted model version {version} to Production")
        
        # Archive old models (keep last 3 versions)
        registry.archive_old_models(keep_versions=3)
        
        logger.info(f"New model deployed successfully")
        logger.info(f"  - Model path: {current_model_path}")
        logger.info(f"  - Scaler path: {scaler_path}")
        logger.info(f"  - Metadata path: {metadata_path}")
        logger.info(f"  - MLflow version: {version}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error deploying new model: {e}")
        return False

@task
async def send_retraining_notification(success: bool, model_info: Dict[str, any] = None) -> None:
    """Send notification about retraining results"""
    logger = get_run_logger()
    
    try:
        if success and model_info:
            performance = model_info['performance']
            run_id = model_info.get('mlflow_run_id', 'N/A')
            model_version = model_info.get('model_version', 'N/A')
            
            message = f"""
🤖 **MODEL RETRAINING COMPLETED** 🤖

✅ **Status**: Successfully deployed new model
📊 **Performance**:
  • Accuracy: {performance['accuracy']:.1%}
  • Precision: {performance['precision']:.1%}
  • Recall: {performance['recall']:.1%}
  • F1 Score: {performance['f1_score']:.1%}

📈 **Training Data**: {model_info['training_samples']} samples
🔄 **MLflow Run ID**: {run_id[:8]}...
📋 **Model Version**: {model_version}
🕒 **Timestamp**: {model_info['timestamp']}

The system is now using the updated model for anomaly detection.
You can view the experiment details at: http://localhost:5000
            """
        else:
            message = f"""
❌ **MODEL RETRAINING FAILED** ❌

The automated model retraining process encountered an error.
The system is continuing to use the previous model.

Please check the logs for more details.
🕒 **Timestamp**: {datetime.now().isoformat()}
            """
        
        await send_telegram_alert_async(message)
        logger.info("Retraining notification sent successfully")
        
        # Log to MLflow for tracking
        if success and model_info:
            with mlflow.start_run(run_name="retraining_notification"):
                mlflow.log_param("notification_type", "success")
                mlflow.log_param("model_version", model_info.get('model_version', 'N/A'))
                mlflow.log_metric("notification_sent", 1)
        
    except Exception as e:
        logger.error(f"Error sending retraining notification: {e}")

@flow(name="Automated Model Retraining", log_prints=True)
async def automated_model_retraining_flow():
    """Main flow for automated model retraining"""
    logger = get_run_logger()
    logger.info("Starting automated model retraining pipeline...")
    
    try:
        # Step 1: Collect training data
        training_data, sample_count = await collect_training_data()
        
        if sample_count < 100:
            logger.warning(f"Insufficient training data ({sample_count} samples). Skipping retraining.")
            return
        
        # Step 2: Detect data drift
        drift_metrics = await detect_data_drift(training_data)
        
        # Step 3: Evaluate current model performance
        performance_metrics = await evaluate_model_performance()
        
        # Step 4: Decide if retraining is needed
        should_retrain = await should_retrain_model(drift_metrics, performance_metrics)
        
        if not should_retrain:
            logger.info("Model retraining not required. Current model is performing well.")
            return
        
        # Step 5: Train new model
        model_info = await train_new_model(training_data)
        
        # Step 6: Validate new model
        validation_passed = await validate_new_model(model_info)
        
        if not validation_passed:
            logger.error("New model validation failed. Keeping current model.")
            await send_retraining_notification(False)
            return
        
        # Step 7: Deploy new model
        deployment_success = await deploy_new_model(model_info)
        
        # Step 8: Send notification
        await send_retraining_notification(deployment_success, model_info)
        
        if deployment_success:
            logger.info("Automated model retraining completed successfully!")
        else:
            logger.error("Model deployment failed!")
            
    except Exception as e:
        logger.error(f"Error in automated retraining flow: {e}")
        await send_retraining_notification(False)
        raise

if __name__ == "__main__":
    # Run the retraining flow
    import asyncio
    asyncio.run(automated_model_retraining_flow())