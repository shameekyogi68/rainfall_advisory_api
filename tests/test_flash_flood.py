import sys
import os
import unittest
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from app.backend import build_farmer_response

class TestPrecisionLogic(unittest.TestCase):
    
    def test_flash_flood_detection(self):
        """Test that High Intensity (>15mm/hr) triggers Flash Flood ALERT"""
        print("\nTesting Flash Flood Logic...")
        
        # Scenario: Normal daily volume (40mm) but EXTREME intensity (20mm in 1 hour)
        response = build_farmer_response(
            ml_category="Normal",
            forecast_7day_mm=40.0,
            taluk="udupi",
            geo_confidence="high",
            confidences={"Normal": 0.8},
            uncertainty_data=None,
            max_intensity_mm_per_hr=20.0 # <--- CRITICAL FEATURE
        )
        
        status = response['main_status']
        print(f"Status: {status['priority']}")
        print(f"Title: {status['title']}")
        
        self.assertEqual(status['priority'], "CRITICAL")
        self.assertEqual(status['title'], "FLASH FLOOD")
        print("✅ Flash Flood detected correctly")

    def test_safe_heavy_rain(self):
        """Test that High Volume but LOW Intensity is NOT a Flash Flood"""
        print("\nTesting Safe Heavy Rain...")
        
        # Scenario: High volume (80mm) but spread out (max 3mm/hr) -> Just Heavy Rain
        response = build_farmer_response(
            ml_category="Excess",
            forecast_7day_mm=80.0,
            taluk="udupi",
            geo_confidence="high",
            confidences={"Excess": 0.8},
            uncertainty_data=None,
            max_intensity_mm_per_hr=3.0 # <--- LOW INTENSITY
        )
        
        status = response['main_status']
        print(f"Status: {status['priority']}")
        print(f"Title: {status['title']}")
        
        # Should be FLOOD (due to volume) but NOT Flash Flood
        # Logic in rules.py maps >60mm to FLOOD/HIGH severity
        self.assertIn(status['title'], ["FLOOD", "HEAVY RAIN"]) 
        # Ideally checks it's not "FLASH FLOOD"
        self.assertNotEqual(status['title'], "FLASH FLOOD")
        print("✅ Heavy Rain distinguished from Flash Flood")

if __name__ == '__main__':
    unittest.main()
