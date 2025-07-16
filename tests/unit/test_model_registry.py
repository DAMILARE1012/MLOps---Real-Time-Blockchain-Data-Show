"""
Unit tests for model registry functionality
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from anomaly_detection.model_registry import ModelRegistry
except ImportError:
    pytest.skip("ModelRegistry not available", allow_module_level=True)


class TestModelRegistry:
    """Test cases for model registry functionality"""
    
    @pytest.fixture
    def mock_mlflow_client(self):
        """Mock MLflow client for testing"""
        with patch('anomaly_detection.model_registry.MlflowClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def sample_model_versions(self):
        """Sample model version data"""
        return [
            {
                "version": "1",
                "stage": "Production",
                "creation_time": 1640995200000,  # 2022-01-01
                "run_id": "run123",
                "status": "READY"
            },
            {
                "version": "2", 
                "stage": "Staging",
                "creation_time": 1641081600000,  # 2022-01-02
                "run_id": "run456",
                "status": "READY"
            }
        ]
    
    def test_registry_initialization(self, mock_mlflow_client):
        """Test model registry initialization"""
        registry = ModelRegistry()
        assert registry.model_name == "blockchain_anomaly_detector"
        assert hasattr(registry, 'client')
    
    def test_get_model_versions(self, mock_mlflow_client, sample_model_versions):
        """Test getting model versions"""
        # Mock the search_model_versions response
        mock_versions = []
        for version_data in sample_model_versions:
            mock_version = MagicMock()
            mock_version.version = version_data["version"]
            mock_version.current_stage = version_data["stage"]
            mock_version.creation_timestamp = version_data["creation_time"]
            mock_version.run_id = version_data["run_id"]
            mock_version.status = version_data["status"]
            mock_versions.append(mock_version)
        
        mock_mlflow_client.search_model_versions.return_value = mock_versions
        
        registry = ModelRegistry()
        versions = registry.get_model_versions()
        
        assert len(versions) == 2
        assert versions[0]["version"] == "2"  # Should be sorted by version desc
        assert versions[1]["version"] == "1"
    
    def test_register_model(self, mock_mlflow_client):
        """Test model registration"""
        with patch('anomaly_detection.model_registry.mlflow.register_model') as mock_register:
            mock_version = MagicMock()
            mock_version.version = "3"
            mock_register.return_value = mock_version
            
            registry = ModelRegistry()
            version = registry.register_model("run789", "model_path")
            
            assert version == "3"
            mock_register.assert_called_once()
    
    def test_promote_model(self, mock_mlflow_client):
        """Test model promotion"""
        registry = ModelRegistry()
        result = registry.promote_model("2", "Production")
        
        assert result is True
        mock_mlflow_client.transition_model_version_stage.assert_called_once_with(
            name="blockchain_anomaly_detector",
            version="2",
            stage="Production"
        )
    
    def test_model_comparison(self, mock_mlflow_client):
        """Test model comparison functionality"""
        # Create sample test data
        test_data = pd.DataFrame({
            'total_value': [10000, 20000, 30000],
            'fee': [100, 200, 300],
            'input_count': [1, 2, 1],
            'output_count': [2, 1, 2]
        })
        
        # Mock model loading
        with patch('anomaly_detection.model_registry.mlflow.sklearn.load_model') as mock_load:
            mock_model1 = MagicMock()
            mock_model1.predict.return_value = np.array([1, -1, 1])
            mock_model1.decision_function.return_value = np.array([0.1, -0.5, 0.2])
            
            mock_model2 = MagicMock()
            mock_model2.predict.return_value = np.array([1, -1, -1])
            mock_model2.decision_function.return_value = np.array([0.05, -0.6, -0.1])
            
            mock_load.side_effect = [mock_model1, mock_model2]
            
            registry = ModelRegistry()
            comparison = registry.compare_models("1", "2", test_data)
            
            assert "version1" in comparison
            assert "version2" in comparison
            assert "agreement_rate" in comparison
    
    def test_archive_old_models(self, mock_mlflow_client, sample_model_versions):
        """Test archiving old models"""
        # Mock get_model_versions to return more than 3 versions
        extended_versions = sample_model_versions + [
            {"version": "3", "stage": "None"},
            {"version": "4", "stage": "None"},
            {"version": "5", "stage": "None"}
        ]
        
        with patch.object(ModelRegistry, 'get_model_versions') as mock_get_versions:
            mock_get_versions.return_value = extended_versions
            
            registry = ModelRegistry()
            registry.archive_old_models(keep_versions=2)
            
            # Should archive versions beyond the keep limit
            expected_calls = 1  # Version 3 should be archived (keep 4,5)
            assert mock_mlflow_client.transition_model_version_stage.call_count >= expected_calls
    
    def test_get_performance_history(self, mock_mlflow_client):
        """Test getting model performance history"""
        # Mock model versions
        mock_versions = [
            {
                "version": "1",
                "stage": "Production", 
                "run_id": "run123"
            }
        ]
        
        # Mock run data
        mock_run = MagicMock()
        mock_run.data.metrics = {
            "anomaly_rate": 0.02,
            "mean_anomaly_score": -0.1
        }
        mock_run.data.params = {
            "contamination": "0.01",
            "n_features": "4"
        }
        
        mock_mlflow_client.get_run.return_value = mock_run
        
        with patch.object(ModelRegistry, 'get_model_versions') as mock_get_versions:
            mock_get_versions.return_value = mock_versions
            
            registry = ModelRegistry()
            history_df = registry.get_model_performance_history()
            
            assert not history_df.empty
            assert "version" in history_df.columns
            assert "anomaly_rate" in history_df.columns


class TestModelRegistryEdgeCases:
    """Test edge cases and error handling"""
    
    def test_registry_with_no_models(self, mock_mlflow_client):
        """Test registry when no models exist"""
        mock_mlflow_client.search_model_versions.return_value = []
        
        registry = ModelRegistry()
        versions = registry.get_model_versions()
        
        assert versions == []
    
    def test_load_nonexistent_production_model(self, mock_mlflow_client):
        """Test loading production model when none exists"""
        with patch('anomaly_detection.model_registry.mlflow.sklearn.load_model') as mock_load:
            mock_load.side_effect = Exception("Model not found")
            
            registry = ModelRegistry()
            model = registry.get_production_model()
            
            assert model is None
    
    def test_failed_model_registration(self, mock_mlflow_client):
        """Test handling of failed model registration"""
        with patch('anomaly_detection.model_registry.mlflow.register_model') as mock_register:
            mock_register.side_effect = Exception("Registration failed")
            
            registry = ModelRegistry()
            
            with pytest.raises(Exception):
                registry.register_model("run123", "model_path")


if __name__ == "__main__":
    pytest.main([__file__])