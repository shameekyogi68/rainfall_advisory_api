
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.backend import process_advisory_request
from app.core.advisory import AdvisoryService

def generate_example():
    # --- INPUT ---
    request_data = {
        "user_id": "farmer_udupi_001",
        "gps_lat": 13.34,
        "gps_long": 74.74,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "crop": "areca"
    }
    
    # --- PROCESSING ---
    # 1. Backend processing
    result = process_advisory_request(
        request_data["user_id"], 
        request_data["gps_lat"], 
        request_data["gps_long"], 
        request_data["date"]
    )
    
    # 2. Enhanced Advisory
    service = AdvisoryService()
    history = result.get('technical_details', {}).get('rainfall_history', [0]*14)
    
    enhanced_response = service.generate_complete_advisory(
        result, 
        request_data["gps_lat"], 
        request_data["gps_long"], 
        crops=[request_data["crop"]],
        rainfall_history=history
    )
    
    # --- OUTPUT ---
    print("### API REQUEST (Input)")
    print("```json")
    print(json.dumps(request_data, indent=2))
    print("```")
    
    print("\n### API RESPONSE (Output)")
    print("```json")
    print(json.dumps(enhanced_response, indent=2, ensure_ascii=False))
    print("```")

if __name__ == "__main__":
    generate_example()
