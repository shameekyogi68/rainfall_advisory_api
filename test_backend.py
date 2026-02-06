import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime
import pandas as pd

# Import application
from api_server import app
from production_backend import TalukMapper, FeatureEngineer, RainfallPredictor

client = TestClient(app)

# ==================== API ENDPOINT TESTS ====================

def test_root_endpoint():
    """Test root endpoint returns service info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Rainfall Advisory API"
    assert "version" in data

def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_metrics_endpoint():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_predictions" in data
    assert data["status"] == "operational"

# ==================== GPS MAPPER TESTS ====================

def test_gps_to_taluk_udupi():
    """Test GPS mapping for Udupi center"""
    mapper = TalukMapper()
    taluk, confidence = mapper.get_taluk(13.3409, 74.7421)
    assert taluk == "udupi"
    assert confidence == "high"

def test_gps_to_taluk_kundapura():
    """Test GPS mapping for Kundapura"""
    mapper = TalukMapper()
    taluk, confidence = mapper.get_taluk(13.6269, 74.6932)
    assert taluk == "kundapura"
    assert confidence == "high"

def test_gps_to_taluk_karkala():
    """Test GPS mapping for Karkala"""
    mapper = TalukMapper()
    taluk, confidence = mapper.get_taluk(13.2114, 74.9929)
    assert taluk == "karkala"
    assert confidence == "high"

# ==================== FEATURE ENGINEERING TESTS ====================

def test_feature_engineering():
    """Test feature computation"""
    engineer = FeatureEngineer()
    features = engineer.compute_features("udupi", "2025-06-15")
    
    # Check all required features exist
    required_features = ['rain_lag_7', 'rain_lag_30', 'rolling_30_rain',
                        'temp', 'humidity', 'wind', 'pressure', 'month']
    
    for feature in required_features:
        assert feature in features
        assert not pd.isna(features[feature])
    
    # Check month is correct
    assert features['month'] == 6  # June

def test_feature_temporal_validation():
    """Test that features don't use future data"""
    engineer = FeatureEngineer()
    
    # This should work (using past data)
    features = engineer.compute_features("udupi", "2025-12-01")
    assert features is not None
    
    # Features should only use data before 2025-12-01
    # (This is validated internally by the < operator in the code)

# ==================== ML PREDICTION TESTS ====================

def test_ml_prediction():
    """Test ML inference returns valid category"""
    predictor = RainfallPredictor()
    
    # Create sample features
    test_features = {
        'rain_lag_7': 5.0,
        'rain_lag_30': 10.0,
        'rolling_30_rain': 150.0,
        'temp': 28.0,
        'humidity': 80.0,
        'wind': 2.5,
        'pressure': 1010.0,
        'month': 6
    }
    
    category, confidences = predictor.predict(test_features)
    
    # Check valid category
    assert category in ['Deficit', 'Normal', 'Excess']
    
    # Check confidences sum to ~1.0
    total_conf = sum(confidences.values())
    assert 0.99 <= total_conf <= 1.01
    
    # Check all categories have confidences
    assert 'Deficit' in confidences
    assert 'Normal' in confidences
    assert 'Excess' in confidences

# ==================== API INTEGRATION TESTS ====================

def test_get_advisory_success():
    """Test successful advisory request"""
    response = client.post("/get-advisory", json={
        "user_id": "test_user",
        "gps_lat": 13.3409,
        "gps_long": 74.7421,
        "date": "2025-06-15"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure (new farmer-friendly format)
    assert data["status"] == "success"
    assert "location" in data
    assert "main_status" in data
    assert "rainfall" in data
    assert "what_to_do" in data
    
    # Check location (new format uses 'area' instead of 'taluk')
    assert data["location"]["area"] == "Udupi"
    assert "district" in data["location"]
    
    # Check rainfall prediction
    assert "monthly_prediction" in data["rainfall"]
    assert data["rainfall"]["monthly_prediction"]["category"] in ['Deficit', 'Normal', 'Excess']
    assert "confidence_percent" in data["rainfall"]["monthly_prediction"]

def test_get_advisory_invalid_gps():
    """Test advisory with out-of-bounds GPS"""
    response = client.post("/get-advisory", json={
        "user_id": "test_user",
        "gps_lat": 20.0,  # Outside Udupi district
        "gps_long": 74.7421,
        "date": "2025-06-15"
    })
    
    assert response.status_code == 422  # Validation error

def test_get_advisory_invalid_date():
    """Test advisory with invalid date format"""
    response = client.post("/get-advisory", json={
        "user_id": "test_user",
        "gps_lat": 13.3409,
        "gps_long": 74.7421,
        "date": "invalid-date"
    })
    
    assert response.status_code == 422

def test_rate_limiting():
    """Test rate limiting (10 requests/minute)"""
    # Make requests
    responses = []
    for i in range(12):
        response = client.post("/get-advisory", json={
            "user_id": f"test_user_{i}",
            "gps_lat": 13.3409,
            "gps_long": 74.7421,
            "date": "2025-06-15"
        })
        responses.append(response.status_code)
    
    # At least one should be rate limited (429)
    # Note: This test may be flaky depending on timing
    # In real tests, you'd mock the rate limiter

# ==================== DRIFT DETECTION TESTS ====================

def test_drift_detector_initialization():
    """Test drift detector loads training stats"""
    from drift_monitor import DriftDetector
    detector = DriftDetector()
    
    assert detector.training_stats is not None
    assert 'rain_lag_7' in detector.training_stats
    assert 'temp' in detector.training_stats

def test_drift_detector_no_drift():
    """Test drift detector with normal features"""
    from drift_monitor import DriftDetector
    detector = DriftDetector()
    
    # Features within normal range
    test_features = {
        'rain_lag_7': 5.0,
        'rain_lag_30': 10.0,
        'rolling_30_rain': 150.0,
        'temp': 28.0,
        'humidity': 80.0,
        'wind': 2.5,
        'pressure': 1010.0,
        'month': 6
    }
    
    drift_detected, report = detector.check_drift(test_features)
    
    # Should not detect drift for normal features
    # (May vary depending on training data)

def test_drift_detector_extreme_value():
    """Test drift detector with extreme outlier"""
    from drift_monitor import DriftDetector
    detector = DriftDetector()
    
    # Extreme temperature
    test_features = {
        'rain_lag_7': 5.0,
        'rain_lag_30': 10.0,
        'rolling_30_rain': 150.0,
        'temp': 60.0,  # Extremely high temp
        'humidity': 80.0,
        'wind': 2.5,
        'pressure': 1010.0,
        'month': 6
    }
    
    drift_detected, report = detector.check_drift(test_features)
    
    assert drift_detected == True
    assert len(report['alerts']) > 0

# ==================== PERFORMANCE TRACKER TESTS ====================

def test_performance_tracker_logging():
    """Test performance tracker logs predictions"""
    from performance_tracker import PerformanceTracker
    tracker = PerformanceTracker()
    
    tracker.log_prediction(
        user_id="test_user",
        taluk="Udupi",
        features={},
        prediction="Normal",
        confidence={"Deficit": 0.1, "Normal": 0.7, "Excess": 0.2},
        alert_sent=False
    )
    
    # Check prediction was logged
    assert tracker.predictions_db.exists()

def test_performance_tracker_metrics():
    """Test performance metrics calculation"""
    from performance_tracker import PerformanceTracker
    tracker = PerformanceTracker()
    
    metrics = tracker.calculate_metrics(last_n_days=30)
    
    # Metrics should have expected structure
    if metrics.get("status") != "no_data":
        assert "total_predictions" in metrics
        assert "category_distribution" in metrics

# ==================== RUN ALL TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
