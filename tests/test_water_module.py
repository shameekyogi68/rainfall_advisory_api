
import sys
import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.advisory import AdvisoryService
from app.backend import build_farmer_response

class TestWaterModule(unittest.TestCase):
    
    def setUp(self):
        self.service = AdvisoryService()
        
    def test_soil_moisture_estimation(self):
        print("\nTesting Soil Moisture Estimation (API Method)...")
        # Test Case 1: Bone Dry (0mm rain for 7 days)
        # API should be 0
        status, index = self.service.estimate_soil_moisture([0]*14)
        print(f"  Input: 0mm/14days -> Status: {status}, Index: {index:.2f}")
        self.assertEqual(status, 'extremely_dry')
        self.assertLess(index, 2.0)
        
        # Test Case 2: Heavy Rain Yesterday (100mm)
        # API ~ 100 * 0.85 = 85 -> Saturated (>50)
        history = [0]*13 + [100] # heavy rain recently
        status, index = self.service.estimate_soil_moisture(history)
        print(f"  Input: 100mm Yesterday -> Status: {status}, Index: {index:.2f}")
        self.assertEqual(status, 'saturated')
        
        # Test Case 3: Moderate Rain (10mm daily for 3 days)
        # API ~ 10*.85 + 10*.85^2 + 10*.85^3 ~ 8.5 + 7.2 + 6.1 = 21.8 -> Wet (>20)
        history = [0]*11 + [10, 10, 10]
        status, index = self.service.estimate_soil_moisture(history)
        print(f"  Input: 10mm/3days -> Status: {status}, Index: {index:.2f}")
        self.assertIn(status, ['wet', 'moist'])

    def test_water_source_advice(self):
        print("\nTesting Water Source Advice...")
        # Mock datetime to test different months
        with patch('app.core.advisory.datetime') as mock_date:
            # Summer (May)
            mock_date.now.return_value = datetime(2025, 5, 15)
            advice = self.service.get_water_source_advice()
            print(f"  May -> {advice}")
            self.assertEqual(advice, 'groundwater_stress')
            
            # Monsoon (July)
            mock_date.now.return_value = datetime(2025, 7, 15)
            advice = self.service.get_water_source_advice()
            print(f"  July -> {advice}")
            self.assertEqual(advice, 'rain_fed')
            
            # Winter (December)
            mock_date.now.return_value = datetime(2025, 12, 15)
            advice = self.service.get_water_source_advice()
            print(f"  December -> {advice}")
            self.assertEqual(advice, 'canal')

    def test_quantitative_irrigation(self):
        print("\nTesting Quantitative Irrigation...")
        # Paddy in Deficit
        qty = self.service.get_quantitative_water_guide('paddy', 'Deficit')
        print(f"  Paddy (Deficit) -> {qty}")
        self.assertEqual(qty, 200000)
        
        # Paddy in Normal (supplemental)
        qty = self.service.get_quantitative_water_guide('paddy', 'Normal')
        print(f"  Paddy (Normal) -> {qty}")
        self.assertEqual(qty, 100000)
        
        # Paddy in Excess
        qty = self.service.get_quantitative_water_guide('paddy', 'Excess')
        print(f"  Paddy (Excess) -> {qty}")
        self.assertEqual(qty, 0)

    def test_full_response_structure(self):
        print("\nTesting Full Response Structure (backend)...")
        # Improve mock to include generate_alert
        with patch('app.core.rules.generate_alert') as mock_alert, \
             patch('app.core.advisory.AdvisoryService.get_risk_level') as mock_risk:
            
            mock_alert.return_value = {
                'status': 'OK', 'severity': 'LOW', 'type': 'NORMAL',
                'sms_text': {'en': 'ok'}, 'whatsapp_text': {'en': 'ok'}
            }
            mock_risk.return_value = ('LOW', '🟢', {'en': 'ok'})
            
            history = [0]*14
            resp = build_farmer_response(
                ml_category='Normal', 
                forecast_7day_mm=10.0,
                taluk='udupi',
                geo_confidence='high',
                confidences={'Normal': 0.8},
                rainfall_history=history
            )
            
            self.assertIn('water_insights', resp)
            self.assertIn('soil_moisture', resp['water_insights'])
            self.assertIn('water_source', resp['water_insights'])
            self.assertIn('technical_details', resp)
            self.assertIn('rainfall_history', resp['technical_details'])
            print("  water_insights present: YES")
            print("  technical_details.rainfall_history present: YES")

if __name__ == '__main__':
    unittest.main()
