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
        alert["sms_text"] = {
            "en": "CRITICAL: Heavy rain (>100mm) expected next 7 days. Flood risk high. Check drainage.",
            "kn": "ತುರ್ತು: ಮುಂದಿನ 7 ದಿನಗಳಲ್ಲಿ ಭಾರೀ ಮಳೆ (>100mm) ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ. ಪ್ರವಾಹದ ಸಾಧ್ಯತೆಯಿದೆ. ಚರಂಡಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."
        }
        alert["whatsapp_text"] = {
            "en": "🚨 *FLOOD WARNING*\n\nHeavy rain (>100mm) predicted for next 7 days.\n\n*Action Required:*\n- Clear drainage channels\n- Delay fertilizer application\n- Secure equipment",
            "kn": "🚨 *ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆ*\n\nಮುಂದಿನ 7 ದಿನಗಳಲ್ಲಿ ಭಾರೀ ಮಳೆ (>100mm) ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ.\n\n*ತುರ್ತು ಕ್ರಮಗಳು:*\n- ಚರಂಡಿಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ\n- ರಸಗೊಬ್ಬರ ಹಾಕಬೇಡಿ\n- ಕೃಷಿ ಉಪಕರಣಗಳನ್ನು ಸುರಕ್ಷಿತವಾಗಿಡಿ"
        }
        return alert

    if live_forecast_7day_mm > 60.0:
        # CONFLICT RESOLUTION: Even if ML says "Drought" or "Normal", 60mm+ is wet.
        alert["severity"] = "HIGH"
        alert["type"] = "FLOOD"
        alert["sms_text"] = {
            "en": "WARNING: Heavy rain (~60mm+) expected. Soil saturation likely. Avoid spraying.",
            "kn": "ಎಚ್ಚರಿಕೆ: ಭಾರೀ ಮಳೆ (~60mm+) ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ. ಮಣ್ಣು ತೇವವಾಗಿರುತ್ತದೆ. ಔಷಧಿ ಸಿಂಪಡಿಸಬೇಡಿ."
        }
        alert["whatsapp_text"] = {
            "en": "🟠 *HEAVY RAIN ALERT*\n\nWet week ahead (>60mm predicted). Soil saturation likely.\n\n*Advisory:*\n- Avoid chemical spraying\n- Monitor field water levels",
            "kn": "🟠 *ಭಾರೀ ಮಳೆ ಮುನ್ಸೂಚನೆ*\n\nಮುಂದಿನ ವಾರ ಹೆಚ್ಚು ಮಳೆ (>60mm) ಇರಲಿದೆ.\n\n*ಸಲಹೆ:*\n- ರಾಸಾಯನ ಸಿಂಪಡಿಸಬೇಡಿ\n- ಹೊಲದಲ್ಲಿನ ನೀರಿನ ಮಟ್ಟವನ್ನು ಗಮನಿಸಿ"
        }
        return alert

    # 2. IRRIGATION/DROUGHT LOGIC
    # Relies on ML 'Deficit' signal + Live Confirmation
    if ml_category == "Deficit":
        if live_forecast_7day_mm < 5.0:
            # ML says Dry + Forecast says Dry = High Confidence Drought Risk
            alert["severity"] = "HIGH"
            alert["type"] = "DROUGHT"
            alert["sms_text"] = {
                "en": "ALERT: Dry spell continues. No rain in next 7 days. Start irrigation now.",
                "kn": "ಎಚ್ಚರಿಕೆ: ಮಳೆ ಇಲ್ಲ. ಮುಂದಿನ 7 ದಿನ ಒಣ ಹವೆ ಇರುತ್ತದೆ. ಕೂಡಲೇ ನೀರು ಹಾಯಿಸಿ."
            }
            alert["whatsapp_text"] = {
                "en": "🔴 *IRRIGATION ALERT*\n\nDry spell confirmed. No significant rain forecast for next 7 days.\n\n*Action:*\n- Start irrigation immediately\n- Conserve soil moisture",
                "kn": "🔴 *ನೀರಾವರಿ ಎಚ್ಚರಿಕೆ*\n\nಮುಂದಿನ 7 ದಿನ ಮಳೆ ಇಲ್ಲದಿರುವುದರಿಂದ ಒಣ ಹವೆ ಮುಂದುವರಿಯಲಿದೆ.\n\n*ಕ್ರಮಗಳು:*\n- ತಕ್ಷಣ ನೀರು ಹಾಯಿಸಿ\n- ಮಣ್ಣಿನ ತೇವಾಂಶ ಕಾಪಾಡಿಕೊಳ್ಳಿ"
            }
            return alert
            
        elif live_forecast_7day_mm < 15.0:
            # ML says Dry, but chance of light rain
            alert["severity"] = "MEDIUM"
            alert["type"] = "DROUGHT"
            alert["sms_text"] = {
                "en": "ADVISORY: Moisture stress likely. Light rain only. Monitor soil.",
                "kn": "ಸಲಹೆ: ನೀರಿನ ಕೊರತೆ ಸಾಧ್ಯತೆ. ಸಾಧಾರಣ ಮಳೆ ಮಾತ್ರ. ಮಣ್ಣಿನ ತೇವಾಂಶ ಗಮನಿಸಿ."
            }
            alert["whatsapp_text"] = {
                "en": "🟠 *MOISTURE STRESS ADVISORY*\n\nDeficit rainfall expected. Only light rain (<15mm) forecast.\n\n*Action:*\n- Monitor soil moisture\n- Prepare to irrigate if rain misses",
                "kn": "🟠 *ನೀರಿನ ಕೊರತೆ ಸಾಧ್ಯತೆ*\n\nಕಡಿಮೆ ಮಳೆ (<15mm) ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ.\n\n*ಕ್ರಮಗಳು:*\n- ಮಣ್ಣಿನ ತೇವಾಂಶ ಪರೀಕ್ಷಿಸಿ\n- ಮಳೆ ಬಾರದಿದ್ದರೆ ನೀರು ಹಾಯಿಸಲು ಸಿದ್ಧರಾಗಿರಿ"
            }
            return alert
            
        else:
            # ML says Dry, but good rain coming (Relief)
            alert["severity"] = "LOW"
            alert["type"] = "DROUGHT_RELIEF"
            alert["sms_text"] = {
                "en": "UPDATE: Relief rain expected (>15mm) this week. Delay irrigation.",
                "kn": "ಮಾಹಿತಿ: ಈ ವಾರ ಉತ್ತಮ ಮಳೆ (>15mm) ನಿರೀಕ್ಷೆಯಿದೆ. ನೀರು ಹಾಯಿಸುವುದನ್ನು ತಡೆಹಿಡಿಯಿರಿ."
            }
            alert["whatsapp_text"] = {
                "en": "🟢 *RELIEF RAIN EXPECTED*\n\nDespite dry trends, rain (>15mm) is forecast for this week.\n\n*Action:*\n- Delay irrigation 2-3 days\n- Store rainwater",
                "kn": "🟢 *ಮಳೆ ನಿರೀಕ್ಷೆ*\n\nಭರವಸೆಯ ಮಳೆ (>15mm) ಈ ವಾರ ಬರಲಿದೆ.\n\n*ಕ್ರಮಗಳು:*\n- 2-3 ದಿನ ನೀರು ಹಾಯಿಸಬೇಡಿ\n- ಮಳೆ ನೀರನ್ನು ಸಂಗ್ರಹಿಸಿ"
            }
            return alert

    # 3. NORMAL / EXCESS (Non-Critical)
    if ml_category == "Excess" and live_forecast_7day_mm <= 60.0:
         # FALSE ALARM CHECK: ML says Excess but forecast is normal.
         # Downgrade to Normal/Wet context
         alert["severity"] = "LOW"
         alert["type"] = "WET_NORMAL"
         alert["sms_text"] = {
             "en": "STATUS: Moderate rains expected. Soil moisture healthy.",
             "kn": "ಸ್ಥಿತಿ: ಸಾಧಾರಣ ಮಳೆ ನಿರೀಕ್ಷೆ. ಮಣ್ಣಿನ ತೇವಾಂಶ ಉತ್ತಮವಾಗಿದೆ."
         }
         alert["whatsapp_text"] = {
             "en": "🟢 *GOOD RAINFALL*\n\nConsistent rains expected. Soil moisture is healthy.\n\n*Action:*\n- Continue normal operations",
             "kn": "🟢 *ಉತ್ತಮ ಮಳೆ*\n\nಉತ್ತಮ ಮಳೆ ಸಾಧಾರಣವಾಗಿ ಬರಲಿದೆ. ಮಣ್ಣಿನ ತೇವಾಂಶ ಚೆನ್ನಾಗಿದೆ.\n\n*ಕ್ರಮಗಳು:*\n- ಸಾಧಾರಣ ಕೃಷಿ ಕೆಲಸ ಮುಂದುವರಿಸಿ"
         }
         return alert

    # 4. DATA GAP / UNKNOWN HANDLING
    # If inputs look suspicious (e.g. exactly 0.0 forecast in monsoon could be error, but 0.0 is valid in winter)
    # We rely on the caller to handle nulls, but here we assume valid floats.
    
    # Default Normal
    alert["severity"] = "LOW"
    alert["type"] = "NORMAL"
    alert["sms_text"] = {
        "en": "STATUS: Normal weather conditions. Proceed with standard care.",
        "kn": "ಸ್ಥಿತಿ: ಹವಾಮಾನ ಸಾಧಾರಣವಾಗಿದೆ. ನಿಮ್ಮ ಕೆಲಸ ಮುಂದುವರಿಸಿ."
    }
    alert["whatsapp_text"] = {
        "en": "🟢 *NORMAL CONDITIONS*\n\nWeather patterns are normal.\n\n*Action:*\n- Proceed with standard crop maintenance",
        "kn": "🟢 *ಸಾಧಾರಣ ಹವಾಮಾನ*\n\nಹವಾಮಾನ ಮಾಮೂಲಿಯಾಗಿದೆ.\n\n*ಕ್ರಮಗಳು:*\n- ವಾಡಿಕೆಯಂತೆ ಬೆಳೆ ನಿರ್ವಹಣೆ ಮಾಡಿ"
    }
    
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
