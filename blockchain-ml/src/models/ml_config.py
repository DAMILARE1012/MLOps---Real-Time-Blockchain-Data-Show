"""
Machine Learning Configuration

Configuration for traditional ML models used in the blockchain analysis system
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a specific ML model"""
    name: str
    model_type: str
    hyperparameters: Dict[str, Any]
    feature_columns: List[str]
    target_column: str
    evaluation_metrics: List[str]


# Traditional ML Models Configuration
ANOMALY_DETECTION_MODELS = {
    "isolation_forest": ModelConfig(
        name="Isolation Forest",
        model_type="anomaly_detection",
        hyperparameters={
            "n_estimators": 100,
            "contamination": 0.1,
            "random_state": 42,
            "max_samples": "auto"
        },
        feature_columns=[
            "transaction_size",
            "input_count", 
            "output_count",
            "fee_per_byte",
            "hour_of_day",
            "day_of_week"
        ],
        target_column="is_anomaly",
        evaluation_metrics=["precision", "recall", "f1_score"]
    ),
    
    "one_class_svm": ModelConfig(
        name="One-Class SVM",
        model_type="anomaly_detection", 
        hyperparameters={
            "kernel": "rbf",
            "nu": 0.1,
            "gamma": "scale"
        },
        feature_columns=[
            "transaction_size",
            "input_count",
            "output_count", 
            "fee_per_byte",
            "hour_of_day",
            "day_of_week"
        ],
        target_column="is_anomaly",
        evaluation_metrics=["precision", "recall", "f1_score"]
    ),
    
    "local_outlier_factor": ModelConfig(
        name="Local Outlier Factor",
        model_type="anomaly_detection",
        hyperparameters={
            "n_neighbors": 20,
            "contamination": 0.1,
            "metric": "euclidean"
        },
        feature_columns=[
            "transaction_size",
            "input_count",
            "output_count",
            "fee_per_byte", 
            "hour_of_day",
            "day_of_week"
        ],
        target_column="is_anomaly",
        evaluation_metrics=["precision", "recall", "f1_score"]
    )
}


TRANSACTION_CLASSIFICATION_MODELS = {
    "random_forest": ModelConfig(
        name="Random Forest Classifier",
        model_type="classification",
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "random_state": 42
        },
        feature_columns=[
            "transaction_size",
            "input_count",
            "output_count",
            "fee_per_byte",
            "hour_of_day",
            "day_of_week",
            "address_activity_frequency",
            "avg_transaction_size"
        ],
        target_column="transaction_type",
        evaluation_metrics=["accuracy", "precision_macro", "recall_macro", "f1_macro"]
    ),
    
    "xgboost": ModelConfig(
        name="XGBoost Classifier", 
        model_type="classification",
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42
        },
        feature_columns=[
            "transaction_size",
            "input_count",
            "output_count",
            "fee_per_byte",
            "hour_of_day", 
            "day_of_week",
            "address_activity_frequency",
            "avg_transaction_size"
        ],
        target_column="transaction_type",
        evaluation_metrics=["accuracy", "precision_macro", "recall_macro", "f1_macro"]
    ),
    
    "lightgbm": ModelConfig(
        name="LightGBM Classifier",
        model_type="classification", 
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42
        },
        feature_columns=[
            "transaction_size",
            "input_count",
            "output_count",
            "fee_per_byte",
            "hour_of_day",
            "day_of_week", 
            "address_activity_frequency",
            "avg_transaction_size"
        ],
        target_column="transaction_type",
        evaluation_metrics=["accuracy", "precision_macro", "recall_macro", "f1_macro"]
    )
}


PRICE_PREDICTION_MODELS = {
    "linear_regression": ModelConfig(
        name="Linear Regression",
        model_type="regression",
        hyperparameters={
            "fit_intercept": True,
            "normalize": False
        },
        feature_columns=[
            "transaction_size",
            "network_congestion",
            "fee_trends",
            "whale_activity",
            "exchange_flow",
            "block_time_variance"
        ],
        target_column="price_impact",
        evaluation_metrics=["mse", "mae", "r2_score"]
    ),
    
    "random_forest_regressor": ModelConfig(
        name="Random Forest Regressor",
        model_type="regression",
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "random_state": 42
        },
        feature_columns=[
            "transaction_size",
            "network_congestion", 
            "fee_trends",
            "whale_activity",
            "exchange_flow",
            "block_time_variance"
        ],
        target_column="price_impact",
        evaluation_metrics=["mse", "mae", "r2_score"]
    ),
    
    "xgboost_regressor": ModelConfig(
        name="XGBoost Regressor",
        model_type="regression",
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42
        },
        feature_columns=[
            "transaction_size",
            "network_congestion",
            "fee_trends", 
            "whale_activity",
            "exchange_flow",
            "block_time_variance"
        ],
        target_column="price_impact",
        evaluation_metrics=["mse", "mae", "r2_score"]
    )
}


# Feature Engineering Configuration
FEATURE_CONFIG = {
    "transaction_features": [
        "transaction_size",
        "input_count", 
        "output_count",
        "fee_per_byte",
        "transaction_age"
    ],
    
    "temporal_features": [
        "hour_of_day",
        "day_of_week",
        "day_of_month",
        "month",
        "is_weekend"
    ],
    
    "network_features": [
        "network_congestion",
        "pending_transaction_count",
        "average_block_time",
        "fee_trends"
    ],
    
    "address_features": [
        "address_activity_frequency",
        "avg_transaction_size",
        "total_transaction_volume",
        "unique_addresses_count"
    ],
    
    "market_features": [
        "whale_activity",
        "exchange_flow",
        "mining_reward",
        "difficulty_change"
    ]
}


# Model Training Configuration
TRAINING_CONFIG = {
    "test_size": 0.2,
    "validation_size": 0.2,
    "random_state": 42,
    "cv_folds": 5,
    "scoring": "f1_macro",
    "n_jobs": -1
}


# Model Deployment Configuration
DEPLOYMENT_CONFIG = {
    "model_version": "v1.0.0",
    "model_path": "models/",
    "artifact_path": "artifacts/",
    "model_registry": "mlflow",
    "monitoring_interval": 300,  # 5 minutes
    "drift_threshold": 0.1
} 