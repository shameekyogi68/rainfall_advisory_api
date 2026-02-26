import requests
import json
import sys

BASE_URL = "http://localhost:8000"

CROPS = ["paddy", "coconut", "arecanut", "vegetables", "cashew", "pepper", "banana"]
LANGUAGES = ["en", "kn"]
# Standard location in Udupi
LAT = 13.3409
LON = 74.7421
DATE = "2023-10-25"

def check_for_bilingual_dicts(obj, path=""):
    """Recursively checks if any {en, kn} dicts remain in the object"""
    errors = []
    if isinstance(obj, dict):
        if "en" in obj and "kn" in obj:
            errors.append(f"Leaked bilingual dict at {path}: {obj}")
        for k, v in obj.items():
            errors.extend(check_for_bilingual_dicts(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            errors.extend(check_for_bilingual_dicts(item, f"{path}[{i}]"))
    return errors

def audit_endpoint(endpoint, crop, lang):
    url = f"{BASE_URL}/{endpoint}"
    payload = {
        "user_id": f"audit_{lang}_{crop}",
        "gps_lat": LAT,
        "gps_long": LON,
        "date": DATE,
        "crop": crop,
        "language": lang
    }
    
    print(f"  Testing {endpoint} | Crop: {crop:10} | Lang: {lang} ... ", end="", flush=True)
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code != 200:
            print(f"❌ FAILED (Status {response.status_code})")
            print(f"    Detail: {response.text}")
            return False
            
        data = response.json()
        
        # 1. Check for Leaked Bilingual Dicts
        leaks = check_for_bilingual_dicts(data)
        if leaks:
            print("❌ FAILED (Localization Leaks)")
            for leak in leaks[:3]: # Show first 3
                print(f"    - {leak}")
            return False
            
        # 2. Basic Content Check (e.g. if we requested 'kn', is there any Kannada text where expected?)
        if lang == "kn":
             # Check main_status title/message for kn script characters
             msg = data.get("main_status", {}).get("message", "")
             # Kannada unicode range: \u0C80-\u0CFF
             has_kn = any('\u0c80' <= char <= '\u0cff' for char in str(msg))
             if not has_kn:
                 print("❌ FAILED (No Kannada script found in message)")
                 return False
                 
        print("✅ PASSED")
        return True

    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def run_audit():
    print("="*60)
    print("🌍 BILINGUAL SYSTEM ACCURACY AUDIT")
    print("="*60)
    
    all_success = True
    
    for endpoint in ["get-advisory", "get-enhanced-advisory"]:
        print(f"\n--- Endpoint: {endpoint} ---")
        for lang in LANGUAGES:
            for crop in CROPS:
                success = audit_endpoint(endpoint, crop, lang)
                if not success:
                    all_success = False
                    
    print("\n" + "="*60)
    if all_success:
        print("🎉 AUDIT COMPLETE: 100% ACCURACY ACROSS ALL SCENARIOS")
    else:
        print("🛑 AUDIT COMPLETE: SOME FAILURES DETECTED")
    print("="*60)
    
    return all_success

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
