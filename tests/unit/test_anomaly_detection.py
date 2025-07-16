"""
Unit tests for anomaly detection module
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock
import joblib
from sklearn.ensemble import IsolationForest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from anomaly_detection.train_model import train_anomaly_model


class TestAnomalyDetection:
    """Test cases for anomaly detection functionality"""
    
    @pytest.fixture
    def sample_features(self):
        """Create sample feature data for testing"""
        np.random.seed(42)
        return pd.DataFrame({
            'total_value': np.random.exponential(50000, 100),
            'fee': np.random.exponential(1000, 100),
            'input_count': np.random.poisson(2, 100) + 1,
            'output_count': np.random.poisson(2, 100) + 1
        })
    
    def test_train_anomaly_model_basic(self, sample_features):
        """Test basic model training functionality"""
        with patch('mlflow.start_run') as mock_mlflow, \
             patch('mlflow.log_param'), \
             patch('mlflow.log_metric'), \
             patch('mlflow.sklearn.log_model'), \
             patch('mlflow.log_artifact'), \
             patch('os.makedirs'), \
             patch('joblib.dump'):
            
            # Mock MLflow context manager
            mock_run = MagicMock()
            mock_run.info.run_id = "test_run_id"
            mock_mlflow.return_value.__enter__.return_value = mock_run
            mock_mlflow.return_value.__exit__.return_value = None
            
            model, scores, predictions = train_anomaly_model(
                sample_features, 
                model_path="test_model.pkl"
            )
            
            # Assertions
            assert isinstance(model, IsolationForest)
            assert len(scores) == len(sample_features)
            assert len(predictions) == len(sample_features)
            assert all(pred in [-1, 1] for pred in predictions)
    
    def test_train_anomaly_model_parameters(self, sample_features):
        """Test model training with custom parameters"""
        with patch('mlflow.start_run') as mock_mlflow, \
             patch('mlflow.log_param'), \
             patch('mlflow.log_metric'), \
             patch('mlflow.sklearn.log_model'), \
             patch('mlflow.log_artifact'), \
             patch('os.makedirs'), \
             patch('joblib.dump'):
            
            mock_run = MagicMock()
            mock_run.info.run_id = "test_run_id"
            mock_mlflow.return_value.__enter__.return_value = mock_run
            mock_mlflow.return_value.__exit__.return_value = None
            
            model, scores, predictions = train_anomaly_model(
                sample_features,
                contamination=0.05,
                random_state=123
            )
            
            assert model.contamination == 0.05
            assert model.random_state == 123
    
    def test_anomaly_detection_scores(self, sample_features):
        """Test anomaly score generation"""
        with patch('mlflow.start_run') as mock_mlflow, \
             patch('mlflow.log_param'), \
             patch('mlflow.log_metric'), \
             patch('mlflow.sklearn.log_model'), \
             patch('mlflow.log_artifact'), \
             patch('os.makedirs'), \
             patch('joblib.dump'):
            
            mock_run = MagicMock()
            mock_run.info.run_id = "test_run_id"
            mock_mlflow.return_value.__enter__.return_value = mock_run
            mock_mlflow.return_value.__exit__.return_value = None
            
            model, scores, predictions = train_anomaly_model(sample_features)
            
            # Check score properties
            assert isinstance(scores, np.ndarray)
            assert len(scores) == len(sample_features)
            assert np.isfinite(scores).all()  # No NaN or inf values
    
    def test_feature_validation(self):
        """Test model training with invalid features"""
        # Test with empty dataframe
        empty_df = pd.DataFrame()
        
        with pytest.raises(Exception):
            with patch('mlflow.start_run'), \
                 patch('mlflow.log_param'), \
                 patch('mlflow.log_metric'), \
                 patch('mlflow.sklearn.log_model'), \
                 patch('mlflow.log_artifact'), \
                 patch('os.makedirs'), \
                 patch('joblib.dump'):
                train_anomaly_model(empty_df)
    
    def test_model_serialization(self, sample_features, tmp_path):
        """Test model saving and loading"""
        model_path = tmp_path / "test_model.pkl"
        
        with patch('mlflow.start_run') as mock_mlflow, \
             patch('mlflow.log_param'), \
             patch('mlflow.log_metric'), \
             patch('mlflow.sklearn.log_model'), \
             patch('mlflow.log_artifact'):
            
            mock_run = MagicMock()
            mock_run.info.run_id = "test_run_id"
            mock_mlflow.return_value.__enter__.return_value = mock_run
            mock_mlflow.return_value.__exit__.return_value = None
            
            # Train and save model
            model, scores, predictions = train_anomaly_model(
                sample_features, 
                model_path=str(model_path)
            )
            
            # Verify model was saved
            assert model_path.exists()
            
            # Load and test model
            loaded_model = joblib.load(model_path)
            new_scores = loaded_model.decision_function(sample_features)
            
            # Scores should be identical
            np.testing.assert_array_equal(scores, new_scores)


class TestFeatureExtraction:
    """Test cases for feature extraction"""
    
    def test_feature_columns(self):
        """Test that required feature columns are present"""
        required_features = ['total_value', 'fee', 'input_count', 'output_count']
        
        # This would test your actual feature extraction logic
        # For now, just test the expected column names
        sample_data = {col: [1, 2, 3] for col in required_features}
        df = pd.DataFrame(sample_data)
        
        assert all(col in df.columns for col in required_features)
    
    def test_feature_types(self):
        """Test feature data types"""
        features = pd.DataFrame({
            'total_value': [10000, 20000, 30000],
            'fee': [100, 200, 300],
            'input_count': [1, 2, 3],
            'output_count': [1, 2, 3]
        })
        
        # All features should be numeric
        assert features.select_dtypes(include=[np.number]).shape[1] == 4


if __name__ == "__main__":
    pytest.main([__file__])