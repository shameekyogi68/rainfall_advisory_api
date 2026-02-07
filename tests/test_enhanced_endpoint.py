
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_enhanced_advisory_success():
    """Test successful enhanced advisory request"""
    response = client.post("/get-enhanced-advisory", json={
        "user_id": "test_user_enhanced",
        "gps_lat": 13.3409,
        "gps_long": 74.7421,
        "date": "2025-06-15"
    })
    
    if response.status_code != 200:
        print(f"Error Response: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure from both production_backend and farmer_advisory
    assert "status" in data
    assert "enhanced_advisory" in data
    
    enhanced = data["enhanced_advisory"]
    assert "prediction" in enhanced
    assert "forecast_7day" in enhanced
    assert "daily_schedule" in enhanced
    assert "crop_advice" in enhanced
    
    # Check if crop advice includes default crops
    assert "paddy" in enhanced["crop_advice"]
    assert "coconut" in enhanced["crop_advice"]

def test_enhanced_advisory_invalid_date():
    """Test enhanced advisory with invalid date"""
    response = client.post("/get-enhanced-advisory", json={
        "user_id": "test_user",
        "gps_lat": 13.3409,
        "gps_long": 74.7421,
        "date": "invalid-date"
    })
    
    assert response.status_code == 422
