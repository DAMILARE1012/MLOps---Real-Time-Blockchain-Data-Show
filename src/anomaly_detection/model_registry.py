"""
Model Registry Management for Blockchain Anomaly Detection
Handles model versioning, staging, and deployment lifecycle
"""

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import logging
from datetime import datetime
import pandas as pd
import joblib
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Manages model lifecycle using MLflow Model Registry
    """
    
    def __init__(self, tracking_uri: str = "http://localhost:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()
        self.model_name = "blockchain_anomaly_detector"
        
    def register_model(self, run_id: str, model_path: str = "anomaly_model") -> str:
        """
        Register a model from an MLflow run
        
        Args:
            run_id: MLflow run ID containing the model
            model_path: Path to model within the run
            
        Returns:
            Model version number
        """
        try:
            model_uri = f"runs:/{run_id}/{model_path}"
            model_version = mlflow.register_model(model_uri, self.model_name)
            logger.info(f"Model registered: {self.model_name} version {model_version.version}")
            return model_version.version
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            raise
    
    def get_model_versions(self) -> List[Dict]:
        """
        Get all versions of the registered model
        
        Returns:
            List of model version information
        """
        try:
            model_versions = self.client.search_model_versions(f"name='{self.model_name}'")
            versions_info = []
            
            for version in model_versions:
                versions_info.append({
                    "version": version.version,
                    "stage": version.current_stage,
                    "creation_time": version.creation_timestamp,
                    "run_id": version.run_id,
                    "status": version.status
                })
            
            return sorted(versions_info, key=lambda x: int(x["version"]), reverse=True)
        except Exception as e:
            logger.error(f"Failed to get model versions: {e}")
            return []
    
    def promote_model(self, version: str, stage: str = "Production") -> bool:
        """
        Promote a model version to a specific stage
        
        Args:
            version: Model version to promote
            stage: Target stage (Staging, Production, Archived)
            
        Returns:
            Success status
        """
        try:
            # Transition current model to new stage
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=version,
                stage=stage
            )
            logger.info(f"Model version {version} promoted to {stage}")
            return True
        except Exception as e:
            logger.error(f"Failed to promote model: {e}")
            return False
    
    def get_production_model(self):
        """
        Get the current production model
        
        Returns:
            Loaded model object
        """
        try:
            model_uri = f"models:/{self.model_name}/Production"
            model = mlflow.sklearn.load_model(model_uri)
            logger.info("Loaded production model")
            return model
        except Exception as e:
            logger.error(f"Failed to load production model: {e}")
            return None
    
    def get_staging_model(self):
        """
        Get the current staging model
        
        Returns:
            Loaded model object
        """
        try:
            model_uri = f"models:/{self.model_name}/Staging"
            model = mlflow.sklearn.load_model(model_uri)
            logger.info("Loaded staging model")
            return model
        except Exception as e:
            logger.error(f"Failed to load staging model: {e}")
            return None
    
    def compare_models(self, version1: str, version2: str, test_data: pd.DataFrame) -> Dict:
        """
        Compare two model versions on test data
        
        Args:
            version1: First model version
            version2: Second model version  
            test_data: Test dataset for comparison
            
        Returns:
            Comparison metrics
        """
        try:
            # Load both models
            model1_uri = f"models:/{self.model_name}/{version1}"
            model2_uri = f"models:/{self.model_name}/{version2}"
            
            model1 = mlflow.sklearn.load_model(model1_uri)
            model2 = mlflow.sklearn.load_model(model2_uri)
            
            # Get predictions
            pred1 = model1.predict(test_data)
            pred2 = model2.predict(test_data)
            
            scores1 = model1.decision_function(test_data)
            scores2 = model2.decision_function(test_data)
            
            # Calculate metrics
            anomaly_rate1 = (pred1 == -1).sum() / len(test_data)
            anomaly_rate2 = (pred2 == -1).sum() / len(test_data)
            
            comparison = {
                "version1": version1,
                "version2": version2,
                "version1_anomaly_rate": anomaly_rate1,
                "version2_anomaly_rate": anomaly_rate2,
                "version1_mean_score": scores1.mean(),
                "version2_mean_score": scores2.mean(),
                "version1_std_score": scores1.std(),
                "version2_std_score": scores2.std(),
                "agreement_rate": (pred1 == pred2).mean()
            }
            
            logger.info(f"Model comparison completed: {comparison}")
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare models: {e}")
            return {}
    
    def archive_old_models(self, keep_versions: int = 3):
        """
        Archive old model versions, keeping only the most recent ones
        
        Args:
            keep_versions: Number of recent versions to keep active
        """
        try:
            versions = self.get_model_versions()
            
            # Skip Production and Staging models
            active_versions = [v for v in versions if v["stage"] not in ["Production", "Staging"]]
            
            if len(active_versions) > keep_versions:
                to_archive = active_versions[keep_versions:]
                
                for version_info in to_archive:
                    self.client.transition_model_version_stage(
                        name=self.model_name,
                        version=version_info["version"],
                        stage="Archived"
                    )
                    logger.info(f"Archived model version {version_info['version']}")
                    
        except Exception as e:
            logger.error(f"Failed to archive old models: {e}")
    
    def get_model_performance_history(self) -> pd.DataFrame:
        """
        Get performance history of all model versions
        
        Returns:
            DataFrame with model performance metrics
        """
        try:
            versions = self.get_model_versions()
            performance_data = []
            
            for version_info in versions:
                run_id = version_info["run_id"]
                run = self.client.get_run(run_id)
                
                metrics = run.data.metrics
                params = run.data.params
                
                performance_data.append({
                    "version": version_info["version"],
                    "stage": version_info["stage"],
                    "run_id": run_id,
                    "creation_time": datetime.fromtimestamp(version_info["creation_time"] / 1000),
                    "contamination": params.get("contamination", None),
                    "n_features": params.get("n_features", None),
                    "n_samples": params.get("n_samples", None),
                    "anomaly_rate": metrics.get("anomaly_rate", None),
                    "mean_anomaly_score": metrics.get("mean_anomaly_score", None),
                    "std_anomaly_score": metrics.get("std_anomaly_score", None),
                    "n_anomalies_detected": metrics.get("n_anomalies_detected", None)
                })
            
            return pd.DataFrame(performance_data)
            
        except Exception as e:
            logger.error(f"Failed to get performance history: {e}")
            return pd.DataFrame()

def main():
    """
    Example usage of ModelRegistry
    """
    registry = ModelRegistry()
    
    # Get all model versions
    versions = registry.get_model_versions()
    print(f"Found {len(versions)} model versions")
    
    for version in versions:
        print(f"Version {version['version']}: Stage={version['stage']}, Status={version['status']}")
    
    # Get performance history
    performance_df = registry.get_model_performance_history()
    if not performance_df.empty:
        print("\nModel Performance History:")
        print(performance_df[['version', 'stage', 'anomaly_rate', 'mean_anomaly_score']].to_string(index=False))
    
    # Load production model if available
    prod_model = registry.get_production_model()
    if prod_model:
        print("\n✅ Production model loaded successfully")
    else:
        print("\n⚠️ No production model available")

if __name__ == "__main__":
    main()