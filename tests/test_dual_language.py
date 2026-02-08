import requests
import json
import sys

def test_dual_language():
    url = "http://localhost:8000/get-advisory"
    payload = {
        "user_id": "test_farmer",
        "gps_lat": 13.3409,
        "gps_long": 74.7421,
        "date": "2025-06-15"
    }
    
    try:
        print(f"Testing {url}...")
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            print(f"FAILED: Status code {response.status_code}")
            print(response.text)
            return False
            
        data = response.json()
        
        # Verify Main Status
        main_status = data.get("main_status", {})
        msg = main_status.get("message", {})
        
        if not isinstance(msg, dict):
            print("FAILED: main_status.message is not a dictionary")
            return False
            
        if "en" not in msg or "kn" not in msg:
            print(f"FAILED: Missing languages in main_status.message. Keys found: {list(msg.keys())}")
            return False
            
        print(f"✅ Main Status Message Verified: EN='{msg['en'][:20]}...', KN='{msg['kn'][:20]}...'")
        
        # Verify What To Do
        what_to_do = data.get("what_to_do", {})
        actions = what_to_do.get("actions", {})
        
        # Check immediate actions if present
        if "immediate" in actions and actions["immediate"]:
            first_action = actions["immediate"][0]
            if not isinstance(first_action, dict) or "en" not in first_action or "kn" not in first_action:
                 print("FAILED: Immediate actions not dual-language")
                 return False
            print(f"✅ Immediate Action Verified: EN='{first_action['en'][:20]}...', KN='{first_action['kn'][:20]}...'")
            
        # Check whatsapp summary
        wa_summary = what_to_do.get("whatsapp_summary", {})
        if not isinstance(wa_summary, dict) or "en" not in wa_summary or "kn" not in wa_summary:
            print("FAILED: WhatsApp summary not dual-language")
            return False
        print(f"✅ WhatsApp Summary Verified")

        print("\n🎉 ALL DUAL-LANGUAGE CHECKS PASSED")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_dual_language()
    sys.exit(0 if success else 1)
