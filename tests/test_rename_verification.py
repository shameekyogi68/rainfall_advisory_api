import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app

client = TestClient(app)

def test_get_advisory_new_params():
    """Test /get-advisory with latitude and longitude"""
    payload = {
        "user_id": "test_verification",
        "latitude": 13.34,
        "longitude": 74.74,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "language": "kn"
    }
    response = client.post("/get-advisory", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Verify coordinates are reflected in logs if we had access to them, 
    # but here we just check if it processes successfully
    assert "location" in data

def test_get_enhanced_advisory_new_params():
    """Test /get-enhanced-advisory with latitude and longitude"""
    payload = {
        "user_id": "test_verification_enhanced",
        "latitude": 13.34,
        "longitude": 74.74,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "language": "en",
        "crop": "paddy"
    }
    response = client.post("/get-enhanced-advisory", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "enhanced_advisory" in data

def test_get_advisory_old_params_fail():
    """Test /get-advisory fails with old gps_lat/gps_long params (validation error)"""
    payload = {
        "user_id": "test_old_fail",
        "gps_lat": 13.34,
        "gps_long": 74.74,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    response = client.post("/get-advisory", json=payload)
    # Pydantic will raise a 422 Unprocessable Entity because gps_lat/gps_long are missing
    assert response.status_code == 422
