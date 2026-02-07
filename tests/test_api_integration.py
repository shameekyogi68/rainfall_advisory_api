import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path to import api_server
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app

client = TestClient(app)

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
    # Health check might fail if server isn't running in a way that mocks can handle properly, 
    # but here we use TestClient with app instance, so it should be fine.
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
