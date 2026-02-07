import json

def generate_alert(ml_category, ml_rainfall_mm, live_forecast_7day_mm):
    """
    Refined Decision Logic (V1.1)
    - Adds Confidence/Severity Levels
    - Implements Conservative Flood Override
    - Formats for SMS/WhatsApp
    """
    
    alert = {
        "status": "OK",
        "severity": "LOW",       # LOW, MEDIUM, HIGH, CRITICAL
        "type": "NORMAL",        # NORMAL, DROUGHT, FLOOD
        "sms_text": "",
        "whatsapp_text": ""
    }
    
    # --- LOGIC BOARD ---
    
    # 1. FLOOD LOGIC (Conservative Override)
    # IF live forecast is very high, trigger FLOOD risk regardless of ML (Safety First)
    if live_forecast_7day_mm > 100.0:
        alert["severity"] = "CRITICAL"
        alert["type"] = "FLOOD"
        alert["sms_text"] = "CRITICAL: Heavy rain (>100mm) expected next 7 days. Flood risk high. Check drainage."
        alert["whatsapp_text"] = "🚨 *FLOOD WARNING*\n\nHeavy rain (>100mm) predicted for next 7 days.\n\n*Action Required:*\n- Clear drainage channels\n- Delay fertilizer application\n- Secure equipment"
        return alert

    if live_forecast_7day_mm > 60.0:
        # CONFLICT RESOLUTION: Even if ML says "Drought" or "Normal", 60mm+ is wet.
        alert["severity"] = "HIGH"
        alert["type"] = "FLOOD"
        alert["sms_text"] = "WARNING: Heavy rain (~60mm+) expected. Soil saturation likely. Avoid spraying."
        alert["whatsapp_text"] = "🟠 *HEAVY RAIN ALERT*\n\nWet week ahead (>60mm predicted). Soil saturation likely.\n\n*Advisory:*\n- Avoid chemical spraying\n- Monitor field water levels"
        return alert

    # 2. IRRIGATION/DROUGHT LOGIC
    # Relies on ML 'Deficit' signal + Live Confirmation
    if ml_category == "Deficit":
        if live_forecast_7day_mm < 5.0:
            # ML says Dry + Forecast says Dry = High Confidence Drought Risk
            alert["severity"] = "HIGH"
            alert["type"] = "DROUGHT"
            alert["sms_text"] = "ALERT: Dry spell continues. No rain in next 7 days. Start irrigation now."
            alert["whatsapp_text"] = "🔴 *IRRIGATION ALERT*\n\nDry spell confirmed. No significant rain forecast for next 7 days.\n\n*Action:*\n- Start irrigation immediately\n- Conserve soil moisture"
            return alert
            
        elif live_forecast_7day_mm < 15.0:
            # ML says Dry, but chance of light rain
            alert["severity"] = "MEDIUM"
            alert["type"] = "DROUGHT"
            alert["sms_text"] = "ADVISORY: Moisture stress likely. Light rain only. Monitor soil."
            alert["whatsapp_text"] = "🟠 *MOISTURE STRESS ADVISORY*\n\nDeficit rainfall expected. Only light rain (<15mm) forecast.\n\n*Action:*\n- Monitor soil moisture\n- Prepare to irrigate if rain misses"
            return alert
            
        else:
            # ML says Dry, but good rain coming (Relief)
            alert["severity"] = "LOW"
            alert["type"] = "DROUGHT_RELIEF"
            alert["sms_text"] = "UPDATE: Relief rain expected (>15mm) this week. Delay irrigation."
            alert["whatsapp_text"] = "🟢 *RELIEF RAIN EXPECTED*\n\nDespite dry trends, rain (>15mm) is forecast for this week.\n\n*Action:*\n- Delay irrigation 2-3 days\n- Store rainwater"
            return alert

    # 3. NORMAL / EXCESS (Non-Critical)
    if ml_category == "Excess" and live_forecast_7day_mm <= 60.0:
         # FALSE ALARM CHECK: ML says Excess but forecast is normal.
         # Downgrade to Normal/Wet context
         alert["severity"] = "LOW"
         alert["type"] = "WET_NORMAL"
         alert["sms_text"] = "STATUS: Moderate rains expected. Soil moisture healthy."
         alert["whatsapp_text"] = "🟢 *GOOD RAINFALL*\n\nConsistent rains expected. Soil moisture is healthy.\n\n*Action:*\n- Continue normal operations"
         return alert

    # 4. DATA GAP / UNKNOWN HANDLING
    # If inputs look suspicious (e.g. exactly 0.0 forecast in monsoon could be error, but 0.0 is valid in winter)
    # We rely on the caller to handle nulls, but here we assume valid floats.
    
    # Default Normal
    alert["severity"] = "LOW"
    alert["type"] = "NORMAL"
    alert["sms_text"] = "STATUS: Normal weather conditions. Proceed with standard care."
    alert["whatsapp_text"] = "🟢 *NORMAL CONDITIONS*\n\nWeather patterns are normal.\n\n*Action:*\n- Proceed with standard crop maintenance"
    
    return alert

# --- TEST CASES ---
if __name__ == "__main__":
    test_cases = [
        ("Deficit", 10.0, 2.0),    # critical drought
        ("Deficit", 10.0, 25.0),   # relief rain
        ("Normal", 100.0, 120.0),  # conservative flood override!
        ("Excess", 100.0, 150.0),  # double confirmed flood
        ("Normal", 50.0, 10.0)     # normal
    ]
    
    print("--- 🧪 REFINED DECISION LOGIC TEST ---")
    for cat, rain, forecast in test_cases:
        res = generate_alert(cat, rain, forecast)
        print(f"\nINPUT: ML={cat}, Forecast={forecast}mm")
        print(f"OUTPUT: [{res['severity']}] {res['whatsapp_text'].splitlines()[0]}")
