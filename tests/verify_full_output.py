
import sys
import os
import json
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.backend import process_advisory_request
from app.core.advisory import AdvisoryService

def verify_full_output():
    # Mock data references
    user_id = "test_farmer_1"
    lat = 13.34  # Udupi
    lon = 74.74
    date = datetime.now().strftime("%Y-%m-%d")

    print(f"--- GENERATING FULL ADVISORY FOR {date} ---")

    # 1. Run Basic Pipeline (Backend)
    # We rely on defaults/mocking if DB isn't set up, but let's try running it.
    # Note: process_advisory_request will look for real model files. 
    # If they exist, great. If not, it might fail or return error.
    # Assuming the environment is set up as previous tests passed.
    
    try:
        result = process_advisory_request(user_id, lat, lon, date)
        
        if result['status'] != 'success':
            print(f"Error in basic prediction: {result}")
            return

        # 2. Run Enhanced Advisory (Main Interface)
        service = AdvisoryService()
        history = result.get('technical_details', {}).get('rainfall_history')
        
        enhanced = service.generate_complete_advisory(
            result, 
            lat, 
            lon, 
            crops=['paddy', 'coconut', 'vegetables'],
            rainfall_history=history
        )
        
        # 3. Print Outputs Mapped to Requirements
        print("\n=== VERIFICATION CHECKLIST ===")
        
        # A. Rainfall Info
        print(f"\n[A] RAINFALL INFORMATION")
        print(f"  - Forecast Category: {enhanced.get('prediction', {}).get('category')}")
        print(f"  - Confidence: {enhanced.get('prediction', {}).get('confidence')}%")
        print(f"  - Historical Context: {json.dumps(enhanced.get('historical_context'), indent=2, ensure_ascii=False)}")
        print(f"  - 7-Day Forecast: {len(enhanced.get('forecast_7day', []))} days provided")
        
        # B. Water Availability
        print(f"\n[B] WATER AVAILABILITY")
        # Soil Moisture
        sm = enhanced.get('soil_moisture', {})
        print(f"  - Soil Moisture: Status={sm.get('status')}, Index={sm.get('index')}")
        
        # Irrigation
        print(f"  - Irrigation Schedule: {len(enhanced.get('daily_schedule', []))} entries")
        crop_advice = enhanced.get('crop_advice', {})
        for crop, data in crop_advice.items():
            qty = data.get('water_quantity', {})
            print(f"  - {crop} Quantity: {qty.get('desc', {}).get('en')}")
            
        # Water Source
        print(f"  - Water Source Advice: {enhanced.get('water_source')}")

        # C. Risks & Alerts
        print(f"\n[C] RISKS & ALERTS")
        print(f"  - Weather Alerts: {json.dumps(enhanced.get('weather_alerts'), indent=2)}")
        print(f"  - Quick Decisions: {json.dumps(enhanced.get('quick_decisions'), indent=2)}")
        
        # D. Output Format
        print(f"\n[D] FORMAT CHECK")
        print(f"  - Prediction Confidence Stats: {json.dumps(enhanced.get('prediction_confidence'), indent=2)}")
        
    except Exception as e:
        print(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_full_output()
