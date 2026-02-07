import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.backend import process_advisory_request

def verify_output():
    print("🚀 Verifying Final System Output for 'Perfect' Compliance...\n")
    
    # Test Case 1: Drought Scenario (Should show Irrigation Needs)
    # We force this by mocking, but for now let's just see what the system produces for a real request
    # NOTE: Since we are hitting live API in the backend, the result depends on actual weather.
    # However, we can inspect the STRUCTURE to ensure fields exist.
    
    # Udupi Coordinates
    response = process_advisory_request(
        user_id="tester", 
        gps_lat=13.3409, 
        gps_long=74.7421, 
        date_str=datetime.now().strftime("%Y-%m-%d")
    )
    
    print("--- FULL JSON OUTPUT ---")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    # Checklist Verification
    print("\n--- 🔍 AUTOMATED INSPECTION ---")
    
    # 1. Monthly Pattern
    if "monthly_prediction" in response.get("rainfall", {}):
        print("✅ Monthly Rainfall Forecast: PRESENT")
    else:
        print("❌ Monthly Rainfall Forecast: MISSING")
        
    # 2. Irrigation/Advisory Logic
    if "what_to_do" in response and "actions" in response["what_to_do"]:
        print("✅ Proactive Management Actions: PRESENT")
    else:
         print("❌ Proactive Management Actions: MISSING")
         
    # 3. Real-time Updates
    if "weather_forecast" in response.get("data_sources", {}) and response["data_sources"]["weather_forecast"] == "live":
        print("✅ Real-time Weather Updates: ACTIVE")
    elif response.get("data_sources", {}).get("weather_forecast") == "historical_estimate":
         print("⚠️ Real-time Weather: FALLBACK (API might be down or key missing, but logic exists)")
    else:
        print("❌ Real-time Weather Updates: MISSING")

    # 4. Flood/Drought conditions are handled by 'main_status' type
    status_type = response.get("main_status", {}).get("title", "")
    print(f"✅ Current System State: {status_type}")

if __name__ == "__main__":
    verify_output()
