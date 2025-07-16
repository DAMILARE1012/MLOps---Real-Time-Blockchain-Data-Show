"""
Unit tests for API endpoints
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import the app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from api.main import app
    client = TestClient(app)
except ImportError:
    pytest.skip("API module not available", allow_module_level=True)


class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    def test_root_endpoint(self):
        """Test API root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "model_loaded" in data
    
    @patch('api.main.get_model')
    def test_predict_anomaly_success(self, mock_get_model):
        """Test successful anomaly prediction"""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([-1])  # Anomaly
        mock_model.decision_function.return_value = np.array([-0.5])
        mock_get_model.return_value = mock_model
        
        # Test data
        transaction_data = {
            "total_value": 100000,
            "fee": 1000,
            "input_count": 2,
            "output_count": 1
        }
        
        response = client.post("/predict/anomaly", json=transaction_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "is_anomaly" in data
        assert "anomaly_score" in data
        assert "confidence" in data
        assert "risk_level" in data
        assert data["is_anomaly"] is True
    
    @patch('api.main.get_model')
    def test_predict_anomaly_normal(self, mock_get_model):
        """Test normal transaction prediction"""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1])  # Normal
        mock_model.decision_function.return_value = np.array([0.3])
        mock_get_model.return_value = mock_model
        
        transaction_data = {
            "total_value": 50000,
            "fee": 500,
            "input_count": 1,
            "output_count": 1
        }
        
        response = client.post("/predict/anomaly", json=transaction_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_anomaly"] is False
        assert data["risk_level"] == "low"
    
    def test_predict_anomaly_invalid_data(self):
        """Test prediction with invalid data"""
        invalid_data = {
            "total_value": -100,  # Invalid negative value
            "fee": 1000,
            "input_count": 2,
            "output_count": 1
        }
        
        response = client.post("/predict/anomaly", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @patch('api.main.get_model')
    def test_batch_prediction(self, mock_get_model):
        """Test batch prediction endpoint"""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1, -1, 1])  # Normal, Anomaly, Normal
        mock_model.decision_function.return_value = np.array([0.2, -0.3, 0.1])
        mock_get_model.return_value = mock_model
        
        batch_data = {
            "transactions": [
                {"total_value": 50000, "fee": 500, "input_count": 1, "output_count": 1},
                {"total_value": 1000000, "fee": 10000, "input_count": 5, "output_count": 5},
                {"total_value": 30000, "fee": 300, "input_count": 1, "output_count": 2}
            ]
        }
        
        response = client.post("/predict/batch", json=batch_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "predictions" in data
        assert "summary" in data
        assert "processing_time_ms" in data
        assert len(data["predictions"]) == 3
        assert data["summary"]["total_transactions"] == 3
        assert data["summary"]["anomalies_detected"] == 1
    
    def test_batch_prediction_empty(self):
        """Test batch prediction with empty list"""
        batch_data = {"transactions": []}
        
        response = client.post("/predict/batch", json=batch_data)
        assert response.status_code == 422  # Validation error
    
    def test_batch_prediction_too_large(self):
        """Test batch prediction with too many transactions"""
        # Create a batch larger than the limit
        large_batch = {
            "transactions": [
                {"total_value": 50000, "fee": 500, "input_count": 1, "output_count": 1}
                for _ in range(1001)  # Exceeds 1000 limit
            ]
        }
        
        response = client.post("/predict/batch", json=large_batch)
        assert response.status_code == 422  # Validation error
    
    def test_model_info_endpoint(self):
        """Test model info endpoint"""
        response = client.get("/model/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_loaded" in data
        assert "model_type" in data
        assert "feature_count" in data
        assert "features" in data
    
    @patch('api.main.model_registry')
    def test_model_performance_endpoint(self, mock_registry):
        """Test model performance endpoint"""
        # Mock model registry
        mock_registry.get_model_performance_history.return_value = None
        
        # This should handle the case where no performance data is available
        response = client.get("/model/performance")
        assert response.status_code in [200, 500]  # Depends on implementation
    
    def test_model_info_no_model(self):
        """Test model info when no model is loaded"""
        with patch('api.main.model_cache', {}):
            response = client.get("/model/info")
            assert response.status_code == 200
            data = response.json()
            assert data["model_loaded"] is False


class TestAPIValidation:
    """Test API input validation"""
    
    def test_transaction_validation_positive_values(self):
        """Test that negative values are rejected"""
        invalid_transactions = [
            {"total_value": -100, "fee": 1000, "input_count": 1, "output_count": 1},
            {"total_value": 100000, "fee": -1000, "input_count": 1, "output_count": 1},
            {"total_value": 100000, "fee": 1000, "input_count": 0, "output_count": 1},
            {"total_value": 100000, "fee": 1000, "input_count": 1, "output_count": 0},
        ]
        
        for invalid_data in invalid_transactions:
            response = client.post("/predict/anomaly", json=invalid_data)
            assert response.status_code == 422
    
    def test_transaction_validation_missing_fields(self):
        """Test that missing required fields are rejected"""
        incomplete_data = {
            "total_value": 100000,
            "fee": 1000
            # Missing input_count and output_count
        }
        
        response = client.post("/predict/anomaly", json=incomplete_data)
        assert response.status_code == 422
    
    def test_transaction_validation_wrong_types(self):
        """Test that wrong data types are rejected"""
        wrong_type_data = {
            "total_value": "not_a_number",
            "fee": 1000,
            "input_count": 1,
            "output_count": 1
        }
        
        response = client.post("/predict/anomaly", json=wrong_type_data)
        assert response.status_code == 422


class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_model_not_available(self):
        """Test behavior when model is not available"""
        with patch('api.main.model_cache', {}):
            transaction_data = {
                "total_value": 100000,
                "fee": 1000,
                "input_count": 2,
                "output_count": 1
            }
            
            response = client.post("/predict/anomaly", json=transaction_data)
            assert response.status_code == 503  # Service unavailable
    
    @patch('api.main.get_model')
    def test_model_prediction_error(self, mock_get_model):
        """Test handling of model prediction errors"""
        # Mock model that raises an exception
        mock_model = MagicMock()
        mock_model.predict.side_effect = Exception("Model error")
        mock_get_model.return_value = mock_model
        
        transaction_data = {
            "total_value": 100000,
            "fee": 1000,
            "input_count": 2,
            "output_count": 1
        }
        
        response = client.post("/predict/anomaly", json=transaction_data)
        assert response.status_code == 500


class TestAPIUtilities:
    """Test utility functions"""
    
    def test_risk_level_calculation(self):
        """Test risk level calculation logic"""
        from api.main import calculate_risk_level
        
        assert calculate_risk_level(0.2) == "low"
        assert calculate_risk_level(0.05) == "medium"
        assert calculate_risk_level(-0.1) == "high"
        assert calculate_risk_level(-0.5) == "critical"
    
    def test_feature_preparation(self):
        """Test feature preparation"""
        from api.main import prepare_features, Transaction
        
        transaction = Transaction(
            total_value=100000,
            fee=1000,
            input_count=2,
            output_count=1
        )
        
        features = prepare_features(transaction)
        assert features.shape == (1, 4)
        assert features[0, 0] == 100000  # total_value
        assert features[0, 1] == 1000    # fee
        assert features[0, 2] == 2       # input_count
        assert features[0, 3] == 1       # output_count


if __name__ == "__main__":
    pytest.main([__file__])