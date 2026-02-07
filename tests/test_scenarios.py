import sys
import os
import unittest
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from app.core.rules import generate_alert
from app.backend import RainfallPredictor

class TestSafetyLogic(unittest.TestCase):
    
    def test_flood_override(self):
        """Test that Live Forecast > 100mm triggers FLOOD even if ML says Normal"""
        print("\nTesting Flood Override...")
        # ML says "Normal" (wrong), Live says 120mm (Flood)
        alert = generate_alert(ml_category="Normal", ml_rainfall_mm=50.0, live_forecast_7day_mm=120.0)
        
        self.assertEqual(alert['type'], "FLOOD")
        self.assertEqual(alert['severity'], "CRITICAL")
        print("✅ Critical Flood Override worked")

    def test_heavy_rain_conflict(self):
        """Test that Live Forecast > 60mm triggers FLOOD even if ML says Drought"""
        print("\nTesting Heavy Rain Conflict...")
        # ML says "Deficit" (wrong), Live says 80mm (Heavy Rain)
        alert = generate_alert(ml_category="Deficit", ml_rainfall_mm=10.0, live_forecast_7day_mm=80.0)
        
        self.assertEqual(alert['type'], "FLOOD")
        self.assertEqual(alert['severity'], "HIGH")
        print("✅ Heavy Rain Conflict Resolution worked")

    def test_false_alarm_suppression(self):
        """Test that Live Forecast < 60mm suppresses ML Excess prediction"""
        print("\nTesting False Alarm Suppression...")
        # ML says "Excess" (False Alarm), Live says 40mm (Normal)
        alert = generate_alert(ml_category="Excess", ml_rainfall_mm=150.0, live_forecast_7day_mm=40.0)
        
        self.assertEqual(alert['type'], "WET_NORMAL")
        self.assertEqual(alert['severity'], "LOW")
        print("✅ False Alarm Suppression worked")

    def test_drought_confirmation(self):
        """Test that Drought is only triggered if BOTH ML and Live agree"""
        print("\nTesting Drought Confirmation...")
        # ML says "Deficit", Live says 2mm (Dry) -> CONFIRMED
        alert = generate_alert(ml_category="Deficit", ml_rainfall_mm=10.0, live_forecast_7day_mm=2.0)
        
        self.assertEqual(alert['type'], "DROUGHT")
        self.assertEqual(alert['severity'], "HIGH")
        print("✅ Drought Confirmation worked")

    def test_drought_relief(self):
        """Test that Drought is CANCELED if Live rain is expected"""
        print("\nTesting Drought Relief...")
        # ML says "Deficit", Live says 20mm (Relief Rain)
        alert = generate_alert(ml_category="Deficit", ml_rainfall_mm=10.0, live_forecast_7day_mm=25.0)
        
        self.assertEqual(alert['type'], "DROUGHT_RELIEF")
        self.assertEqual(alert['severity'], "LOW")
        print("✅ Drought Relief logic worked")

    def test_calibration_logic(self):
        """Test the probability calibration logic directly"""
        print("\nTesting Probability Calibration...")
        predictor = RainfallPredictor()
        
        # Scenario: Normal is winning but barely, and Deficit is close
        # Before: Normal=0.45, Deficit=0.35, Excess=0.2
        raw_conf = {'Normal': 0.45, 'Deficit': 0.35, 'Excess': 0.2}
        
        cat, final_conf = predictor.calibrate_prediction(raw_conf)
        
        # After penalty (Normal*0.8 = 0.36) and boost (Deficit*1.3 = 0.455)
        # Deficit should win
        print(f"Raw: {raw_conf}")
        print(f"Calibrated Winner: {cat}")
        print(f"Calibrated Conf: {final_conf}")
        
        self.assertEqual(cat, "Deficit")
        print("✅ Calibration correctly flipped weak Normal to Deficit")

if __name__ == '__main__':
    unittest.main()
