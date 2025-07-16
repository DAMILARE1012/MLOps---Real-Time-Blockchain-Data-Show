import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os
import logging
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# MLflow configuration
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("blockchain_anomaly_detection")

def train_anomaly_model(features: pd.DataFrame, model_path: str = "../../models/anomaly_model.pkl", 
                       contamination: float = 0.01, random_state: int = 42):
    """
    Train anomaly detection model with MLflow tracking
    """
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("algorithm", "IsolationForest")
        mlflow.log_param("contamination", contamination)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("n_features", features.shape[1])
        mlflow.log_param("n_samples", features.shape[0])
        mlflow.log_param("feature_columns", list(features.columns))
        
        # Train model
        model = IsolationForest(contamination=contamination, random_state=random_state)
        model.fit(features)
        
        # Evaluate model
        scores = model.decision_function(features)
        predictions = model.predict(features)
        n_anomalies = (predictions == -1).sum()
        anomaly_rate = n_anomalies / len(features)
        
        # Log metrics
        mlflow.log_metric("n_anomalies_detected", n_anomalies)
        mlflow.log_metric("anomaly_rate", anomaly_rate)
        mlflow.log_metric("mean_anomaly_score", np.mean(scores))
        mlflow.log_metric("std_anomaly_score", np.std(scores))
        mlflow.log_metric("min_anomaly_score", np.min(scores))
        mlflow.log_metric("max_anomaly_score", np.max(scores))
        
        # Log model
        mlflow.sklearn.log_model(
            model, 
            "anomaly_model",
            registered_model_name="blockchain_anomaly_detector"
        )
        
        # Save model locally
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        
        # Log artifacts
        mlflow.log_artifact(model_path, "model_files")
        
        logger.info(f"Model saved to {model_path}")
        logger.info(f"MLflow run ID: {mlflow.active_run().info.run_id}")
        
        return model, scores, predictions

def main():
    features_path = "./historical_features.csv"
    if not os.path.exists(features_path):
        logger.error(f"Features file {features_path} not found. Run feature extraction first.")
        return
    
    features = pd.read_csv(features_path)
    logger.info(f"Loaded {len(features)} feature rows for training.")
    
    # Train model with MLflow tracking
    model, scores, preds = train_anomaly_model(features, model_path="../../models/anomaly_model.pkl")
    
    n_anomalies = (preds == -1).sum()
    logger.info(f"Number of anomalies detected in training data: {n_anomalies}")
    
    # Create and log visualizations
    with mlflow.start_run():
        # Plot anomaly score distribution
        plt.figure(figsize=(12, 8))
        plt.hist(scores, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title("Anomaly Scores Distribution (Higher = More Normal)")
        plt.xlabel("Anomaly Score")
        plt.ylabel("Frequency")
        plt.grid(linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        plot_path = "anomaly_score_distribution.png"
        plt.savefig(plot_path)
        mlflow.log_artifact(plot_path, "plots")
        logger.info(f"Saved anomaly score distribution plot as {plot_path}")
        
        # Anomaly vs Normal distribution
        plt.figure(figsize=(12, 8))
        normal_scores = scores[preds == 1]
        anomaly_scores = scores[preds == -1]
        
        plt.hist(normal_scores, bins=30, alpha=0.7, label='Normal', color='green')
        plt.hist(anomaly_scores, bins=30, alpha=0.7, label='Anomaly', color='red')
        plt.title("Anomaly vs Normal Score Distribution")
        plt.xlabel("Anomaly Score")
        plt.ylabel("Frequency")
        plt.legend()
        plt.grid(linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        comparison_plot_path = "anomaly_vs_normal_distribution.png"
        plt.savefig(comparison_plot_path)
        mlflow.log_artifact(comparison_plot_path, "plots")
        logger.info(f"Saved comparison plot as {comparison_plot_path}")
        
        # Save top anomalies to CSV
        features['anomaly_score'] = scores
        features['is_anomaly'] = preds
        anomalies = features[features['is_anomaly'] == -1]
        anomalies.sort_values('anomaly_score', inplace=True)
        
        top_anomalies_path = "top_anomalies.csv"
        anomalies.head(100).to_csv(top_anomalies_path, index=False)
        mlflow.log_artifact(top_anomalies_path, "data")
        logger.info(f"Saved top 100 anomalies to {top_anomalies_path}")
        
        # Log additional metrics
        mlflow.log_metric("training_data_size", len(features))
        mlflow.log_metric("total_anomalies", n_anomalies)
        mlflow.log_metric("normal_transactions", len(features) - n_anomalies)
        
        logger.info("Training completed with MLflow tracking!")

if __name__ == "__main__":
    main() 