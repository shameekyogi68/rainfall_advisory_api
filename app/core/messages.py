# Farmer-Friendly Output Messages
# Designed for easy translation to Kannada
# Simple language, visual symbols, clear structure

# Message structure for translation:
# {
#   "en": "English text",
#   "kn": "Kannada text",  # To be added
#   "icon": "🔴",
#   "color": "#FF0000"
# }

FARMER_MESSAGES = {
    # === RAINFALL STATUS ===
    "deficit": {
        "status": {
            "en": "DRY SPELL",
            "kn": "ಶುಷ್ಕ ಅವಧಿ",
            "icon": "☀️",
            "color": "#FF0000"
        },
        "title": {
            "en": "Less Rain Expected",
            "kn": "ಕಡಿಮೆ ಮಳೆ ನಿರೀಕ್ಷೆ",
            "icon": "⚠️"
        }
    },
    "normal": {
        "status": {
            "en": "NORMAL",
            "kn": "ಸಾಮಾನ್ಯ",
            "icon": "🌤️",
            "color": "#4CAF50"
        },
        "title": {
            "en": "Normal Rainfall",
            "kn": "ಸಾಮಾನ್ಯ ಮಳೆ",
            "icon": "✅"
        }
    },
    "excess": {
        "status": {
            "en": "HEAVY RAIN",
            "kn": "ಭಾರೀ ಮಳೆ",
            "icon": "🌧️",
            "color": "#2196F3"
        },
        "title": {
            "en": "More Rain Expected",
            "kn": "ಹೆಚ್ಚು ಮಳೆ ನಿರೀಕ್ಷೆ",
            "icon": "💧"
        }
    },
    
    # === ALERT LEVELS ===
    "alert_levels": {
        "safe": {
            "en": "SAFE",
            "kn": "ಸುರಕ್ಷಿತ",
            "icon": "✅",
            "color": "#4CAF50"
        },
        "watch": {
            "en": "BE CAREFUL",
            "kn": "ಎಚ್ಚರ ವಹಿಸಿ",  # Changed from "ಜಾಗರೂಕತೆ" (Noun) to Command
            "icon": "⚠️",
            "color": "#FF9800"
        },
        "warning": {
            "en": "TAKE ACTION",
            "kn": "ಮುನ್ನೆಚ್ಚರಿಕೆ ವಹಿಸಿ", # Better than "ಕ್ರಮ ತೆಗೆದುಕೊಳ್ಳಿ"
            "icon": "🚨",
            "color": "#FF5722"
        },
        "urgent": {
            "en": "URGENT ACTION",
            "kn": "ತುರ್ತು ಕ್ರಮ ಅಗತ್ಯ", # Added "Necessary"
            "icon": "🔴",
            "color": "#D32F2F"
        },
        "danger": {
            "en": "DANGER",
            "kn": "ಅಪಾಯ",
            "icon": "🚨",
            "color": "#D32F2F"
        }
    },
    
    # === SIMPLE ACTIONS ===
    "actions": {
        "irrigate_now": {
            "en": "Give Water to Crops Now",
            "kn": "ಬೆಳೆಗಳಿಗೆ ಕೂಡಲೇ ನೀರು ಹಾಯಿಸಿ", # "Hayisi" is more specific for irrigation
            "icon": "💧"
        },
        "irrigate_prepare": {
            "en": "Keep Water Ready",
            "kn": "ನೀರು ಸಂಗ್ರಹಿಸಿಟ್ಟುಕೊಳ್ಳಿ", # "Store/Keep ready"
            "icon": "🚰"
        },
        "no_irrigate": {
            "en": "No Need to Give Water",
            "kn": "ನೀರಾವರಿ ಅಗತ್ಯವಿಲ್ಲ", # More formal/clear
            "icon": "✋"
        },
        "clean_drainage": {
            "en": "Open/Clean Water Channels",
            "kn": "ನೀರು ಹರಿದು ಹೋಗುವಂತೆ ಕಾಲುವೆ ಮಾಡಿ", # Action oriented: "Make way for water"
            "icon": "🌊"
        },
        "no_spray": {
            "en": "Don't Spray Pesticides",
            "kn": "ಔಷಧಿ ಸಿಂಪಡಿಸಬೇಡಿ", # "Aushadhi" is commonly used
            "icon": "🚫"
        },
        "postpone_fertilizer": {
            "en": "Postpone Fertilizer",
            "kn": "ಗೊಬ್ಬರ ಹಾಕುವುದನ್ನು ಮುಂದುಡಿ",
            "icon": "⏸️"
        },
        "normal_work": {
            "en": "Continue Normal Work",
            "kn": "ನಿಮ್ಮ ಕೃಷಿ ಕೆಲಸ ಮುಂದುವರಿಸಿ",
            "icon": "👍"
        },
        "check_field": {
            "en": "Check Your Field",
            "kn": "ಹೊಲವನ್ನು ಗಮನಿಸಿ", # "Observe the field"
            "icon": "👁️"
        }
    },
    
    # === FARMER-FRIENDLY SCENARIOS ===
    "scenarios": {
        "drought_critical": {
            "title": {
                "en": "No Rain Coming",
                "kn": "ಮಳೆ ಇಲ್ಲ",
                "icon": "🔴"
            },
            "message": {
                "en": "Dry weather for 7 days. Crops need water now.",
                "kn": "ಮುಂದಿನ 7 ದಿನ ಒಣ ಹವೆ ಇರುತ್ತದೆ. ಬೆಳೆಗಳಿಗೆ ಆತ್ಯಂತಿಕವಾಗಿ ನೀರು ಬೇಕಿದೆ.",
            },
            "priority": "URGENT"
        },
        "drought_moderate": {
            "title": {
                "en": "Less Rain Expected",
                "kn": "ಕಡಿಮೆ ಮಳೆ ನಿರೀಕ್ಷೆ",
                "icon": "🟡"
            },
            "message": {
                "en": "Little rain expected. Keep water ready for crops.",
                "kn": "ಸ್ವಲ್ಪ ಮಳೆ ಬರಬಹುದು. ಬೆಳೆಗಳಿಗೆ ನೀರು ಸಿದ್ಧವಿರಲಿ.",
            },
            "priority": "WATCH"
        },
        "flood_critical": {
            "title": {
                "en": "Flash Flood Risk",
                "kn": "ಪ್ರವಾಹ ಭೀತಿ (ಫ್ಲಾಶ್ ಫ್ಲಡ್)",
                "icon": "🔴"
            },
            "message": {
                "en": "Intense rain (>100mm) coming. Drain fields immediately.",
                "kn": "ಭಾರೀ ಮಳೆ (>100mm) ಬರುತ್ತಿದೆ. ಹೊಲದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ನೋಡಿಕೊಳ್ಳಿ.",
            },
            "priority": "URGENT"
        },
        "flood_warning": {
            "title": {
                "en": "Heavy Rain Expected",
                "kn": "ಭಾರೀ ಮಳೆ ಮುನ್ಸೂಚನೆ",
                "icon": "🟠"
            },
            "message": {
                "en": "Heavy rain coming. Soil will be very wet.",
                "kn": "ಭಾರೀ ಮಳೆ ನಿರೀಕ್ಷೆಯಿದೆ. ಮಣ್ಣಿನ ತೇವಾಂಶ ಹೆಚ್ಚಾಗಲಿದೆ.",
            },
            "priority": "WARNING"
        },
        "normal": {
            "title": {
                "en": "Normal Weather",
                "kn": "ಸಾಮಾನ್ಯ ಹವಾಮಾನ",
                "icon": "🟢"
            },
            "message": {
                "en": "Weather is good. Continue your normal farm work.",
                "kn": "ಹವಾಮಾನ ಅನುಕೂಲಕರವಾಗಿದೆ. ಕೃಷಿ ಚಟುವಟಿಕೆ ಮುಂದುವರಿಸಿ.",
            },
            "priority": "SAFE"
        },
        "relief_rain": {
            "title": {
                "en": "Rain Coming Soon",
                "kn": "ಮಳೆ ಬರುವ ಸಾಧ್ಯತೆ",
                "icon": "🟢"
            },
            "message": {
                "en": "Rain is coming soon. Wait 2-3 days before giving water.",
                "kn": "ಮಳೆ ಬರುವ ಸಂಭವವಿದೆ. ನೀರು ಕೊಡುವ ಮೊದಲು 2-3 ದಿನ ಕಾಯಿರಿ.",
            },
            "priority": "SAFE"
        }
    },
    
    # === TIME PERIODS (Simple) ===
    "time": {
        "today": {"en": "Today", "kn": "ಇಂದು"},
        "tomorrow": {"en": "Tomorrow", "kn": "ನಾಳೆ"},
        "this_week": {"en": "This Week", "kn": "ಈ ವಾರ"},
        "next_7_days": {"en": "Next 7 Days", "kn": "ಮುಂದಿನ 7 ದಿನ"}
    },
    
    # === SIMPLE MEASUREMENTS ===
    "measurements": {
        "very_less": {"en": "Very Less", "kn": "ತೀರಾ ಕಡಿಮೆ", "icon": "☀️"},
        "less": {"en": "Less", "kn": "ಕಡಿಮೆ", "icon": "🌤️"},
        "normal": {"en": "Normal", "kn": "ಸಾಮಾನ್ಯ", "icon": "⛅"},
        "more": {"en": "Heavy", "kn": "ಹೆಚ್ಚು", "icon": "🌧️"},
        "very_more": {"en": "Very Heavy", "kn": "ವಿಪರೀತ (ತುಂಬಾ ಹೆಚ್ಚು)", "icon": "⛈️"}
    }
}

def get_farmer_friendly_scenario(ml_category, forecast_7day_mm):
    """
    Convert technical data into farmer-friendly scenario
    Returns scenario key for translation
    """
    # Critical drought
    if ml_category == "Deficit" and forecast_7day_mm < 5:
        return "drought_critical"
    
    # Moderate drought    
    if ml_category == "Deficit" and forecast_7day_mm < 15:
        return "drought_moderate"
    
    # Relief rain
    if ml_category == "Deficit" and forecast_7day_mm >= 15:
        return "relief_rain"
    
    # Critical flood
    if forecast_7day_mm > 100:
        return "flood_critical"
    
    # Heavy rain warning
    if forecast_7day_mm > 60:
        return "flood_warning"
    
    # Normal
    return "normal"

def get_rainfall_category_simple(forecast_mm):
    """Convert mm to simple farmer-friendly category"""
    if forecast_mm < 5:
        return "very_less"
    elif forecast_mm < 20:
        return "less"
    elif forecast_mm < 50:
        return "normal"
    elif forecast_mm < 100:
        return "more"
    else:
        return "very_more"

def get_simple_actions(scenario_key):
    """
    Returns list of action keys based on scenario
    """
    action_map = {
        "drought_critical": ["irrigate_now", "check_field"],
        "drought_moderate": ["irrigate_prepare", "check_field"],
        "relief_rain": ["no_irrigate", "normal_work"],
        "flood_critical": ["clean_drainage", "no_spray", "postpone_fertilizer"],
        "flood_warning": ["clean_drainage", "no_spray"],
        "normal": ["normal_work"]
    }
    
    return action_map.get(scenario_key, ["normal_work"])
