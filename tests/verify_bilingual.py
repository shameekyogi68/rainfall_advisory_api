import requests
import json

def test_language(lang):
    url = "http://localhost:8000/get-advisory"
    payload = {
        "user_id": "test_farmer",
        "gps_lat": 13.3409,
        "gps_long": 74.7421,
        "date": "2023-10-25",
        "language": lang
    }
    
    print(f"\n--- Testing Language: {lang.upper()} ---")
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"FAILED: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        
        # Check main_status.message
        message = data.get("main_status", {}).get("message")
        print(f"Main Message: {message}")
        
        # Check if it's a string (meaning it was localized)
        if not isinstance(message, str):
            print(f"FAILED: Message is not a string, got {type(message)}")
            return
            
        # Check some other fields
        summary = data.get("what_to_do", {}).get("advisory_summary")
        print(f"Advisory Summary: {summary}")
        
        if not isinstance(summary, str):
            print(f"FAILED: Summary is not a string")
            return

        print(f"✅ Language {lang} verified successfully!")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Note: Server must be running for this to work
    test_language("en")
    test_language("kn")
