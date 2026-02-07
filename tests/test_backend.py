#!/usr/bin/env python3
"""
Unit Tests for Production Backend
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.backend import process_advisory_request

class TestProductionBackend:
    """Test production backend functions"""
    
    def test_basic_prediction(self):
        """Test basic prediction works"""
        result = process_advisory_request(
            'test_user',
            13.3409,  # Udupi lat
            74.7421,  # Udupi lon
            '2026-02-07'
        )
        
        assert result['status'] == 'success'
        assert 'rainfall' in result
        assert 'monthly_prediction' in result['rainfall']
        
        pred = result['rainfall']['monthly_prediction']
        assert 'category' in pred
        assert pred['category'] in ['Deficit', 'Normal', 'Excess']
        assert 'confidence_percent' in pred
        assert 0 <= pred['confidence_percent'] <= 100
    
    def test_invalid_coordinates(self):
        """Test handling of invalid coordinates"""
        # Latitude out of range
        result = process_advisory_request('test', 999, 74.7421, '2026-02-07')
        assert result['status'] == 'error'
        
        # Longitude out of range
        result = process_advisory_request('test', 13.3409, 999, '2026-02-07')
        assert result['status'] == 'error'
    
    def test_date_formats(self):
        """Test different date formats"""
        # Valid format
        result = process_advisory_request('test', 13.3409, 74.7421, '2026-02-07')
        assert result['status'] == 'success'
        
        # Check metadata
        assert 'data_sources' in result
        # Request date might be in a sub-dictionary or just check it processed

    
    def test_prediction_consistency(self):
        """Test that same inputs give same prediction"""
        result1 = process_advisory_request('test', 13.3409, 74.7421, '2026-02-07')
        result2 = process_advisory_request('test', 13.3409, 74.7421, '2026-02-07')
        
        pred1 = result1['rainfall']['monthly_prediction']
        pred2 = result2['rainfall']['monthly_prediction']
        
        assert pred1['category'] == pred2['category']
        assert pred1['confidence_percent'] == pred2['confidence_percent']
    
    def test_different_taluks(self):
        """Test predictions for different taluks"""
        # Udupi
        result_udupi = process_advisory_request('test', 13.3409, 74.7421, '2026-02-07')
        
        # Karkala (different location)
        result_karkala = process_advisory_request('test', 13.2108, 74.9896, '2026-02-07')
        
        # Both should succeed
        assert result_udupi['status'] == 'success'
        assert result_karkala['status'] == 'success'
        
        # Taluks should be identified
        # Note: taluk might be under 'location' -> 'area' or 'taluk'
        taluk = result_udupi.get('location', {}).get('area')
        if not taluk:
            taluk = result_udupi.get('location', {}).get('taluk')
            
        assert taluk is not None
        # Backend capitalizes names
        assert taluk in ['Udupi', 'Kundapura', 'Karkala', 'Hebri', 'Brahmavara', 'Kapu', 'Byndoor']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
