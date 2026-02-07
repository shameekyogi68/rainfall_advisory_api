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
            "kn": "ಜಾಗರೂಕತೆ",
            "icon": "⚠️",
            "color": "#FF9800"
        },
        "warning": {
            "en": "TAKE ACTION",
            "kn": "ಕ್ರಮ ತೆಗೆದುಕೊಳ್ಳಿ",
            "icon": "🚨",
            "color": "#FF5722"
        },
        "urgent": {
            "en": "URGENT ACTION",
            "kn": "ತುರ್ತು ಕ್ರಮ",
            "icon": "🔴",
            "color": "#D32F2F"
        },
        "danger": {
            "en": "URGENT ACTION",
            "kn": "ತುರ್ತು ಕ್ರಮ",
            "icon": "🚨",
            "color": "#D32F2F"
        }
    },
    
    # === SIMPLE ACTIONS ===
    "actions": {
        "irrigate_now": {
            "en": "Give Water to Crops Now",
            "kn": "ಈಗಲೇ ಬೆಳೆಗಳಿಗೆ ನೀರು ಕೊಡಿ",
            "icon": "💧"
        },
        "irrigate_prepare": {
            "en": "Keep Water Ready",
            "kn": "ನೀರು ಸಿದ್ಧ ಇಡಿ",
            "icon": "🚰"
        },
        "no_irrigate": {
            "en": "No Need to Give Water",
            "kn": "ನೀರು ಕೊಡಬೇಕಾಗಿಲ್ಲ",
            "icon": "✋"
        },
        "clean_drainage": {
            "en": "Clean Water Channels",
            "kn": "ನೀರು ಕಾಲುವೆಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ",
            "icon": "🌊"
        },
        "no_spray": {
            "en": "Don't Spray Pesticides",
            "kn": "ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಬೇಡಿ",
            "icon": "🚫"
        },
        "postpone_fertilizer": {
            "en": "Wait for Fertilizer",
            "kn": "ಗೊಬ್ಬರ ಹಾಕಲು ಕಾಯಿರಿ",
            "icon": "⏸️"
        },
        "normal_work": {
            "en": "Continue Normal Work",
            "kn": "ಎಂದಿನಂತೆ ಕೆಲಸ ಮುಂದುವರಿಸಿ",
            "icon": "👍"
        },
        "check_field": {
            "en": "Check Your Field",
            "kn": "ನಿಮ್ಮ ಹೊಲ ಪರೀಕ್ಷಿಸಿ",
            "icon": "👁️"
        }
    },
    
    # === FARMER-FRIENDLY SCENARIOS ===
    "scenarios": {
        "drought_critical": {
            "title": {
                "en": "No Rain Coming",
                "kn": "ಮಳೆ ಬರುತ್ತಿಲ್ಲ",
                "icon": "🔴"
            },
            "message": {
                "en": "Dry weather for 7 days. Crops need water now.",
                "kn": "7 ದಿನ ಶುಷ್ಕ ವಾತಾವರಣ. ಬೆಳೆಗೆ ಈಗ ನೀರು ಬೇಕು.",
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
                "kn": "ಸ್ವಲ್ಪ ಮಳೆ ನಿರೀಕ್ಷೆ. ಬೆಳೆಗಾಗಿ ನೀರು ಸಿದ್ಧ ಇಡಿ.",
            },
            "priority": "WATCH"
        },
        "flood_critical": {
            "title": {
                "en": "Very Heavy Rain Coming",
                "kn": "ತುಂಬಾ ಭಾರೀ ಮಳೆ ಬರುತ್ತಿದೆ",
                "icon": "🔴"
            },
            "message": {
                "en": "More than 100mm rain in 7 days. Water may collect in field.",
                "kn": "7 ದಿನದಲ್ಲಿ 100mm ಹೆಚ್ಚು ಮಳೆ. ಹೊಲದಲ್ಲಿ ನೀರು ನಿಲ್ಲಬಹುದು.",
            },
            "priority": "URGENT"
        },
        "flood_warning": {
            "title": {
                "en": "Heavy Rain Expected",
                "kn": "ಭಾರೀ ಮಳೆ ನಿರೀಕ್ಷೆ",
                "icon": "🟠"
            },
            "message": {
                "en": "60-100mm rain coming. Soil will be very wet.",
                "kn": "60-100mm ಮಳೆ ಬರುತ್ತಿದೆ. ಮಣ್ಣು ತುಂಬಾ ಒದ್ದೆಯಾಗುತ್ತದೆ.",
            },
            "priority": "WARNING"
        },
        "normal": {
            "title": {
                "en": "Normal Weather",
                "kn": "ಸಾಮಾನ್ಯ ವಾತಾವರಣ",
                "icon": "🟢"
            },
            "message": {
                "en": "Weather is good. Continue your normal farm work.",
                "kn": "ವಾತಾವರಣ ಚನ್ನಾಗಿದೆ. ನಿಮ್ಮ ಎಂದಿನ ಕೃಷಿ ಕೆಲಸ ಮುಂದುವರಿಸಿ.",
            },
            "priority": "SAFE"
        },
        "relief_rain": {
            "title": {
                "en": "Good News - Rain Coming",
                "kn": "ಶುಭ ಸುದ್ದಿ - ಮಳೆ ಬರುತ್ತಿದೆ",
                "icon": "🟢"
            },
            "message": {
                "en": "Rain is coming soon. Wait 2-3 days before giving water.",
                "kn": "ಮಳೆ ಶೀಘ್ರದಲ್ಲಿ ಬರುತ್ತದೆ. ನೀರು ಕೊಡುವ ಮೊದಲು 2-3 ದಿನ ಕಾಯಿರಿ.",
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
        "very_less": {"en": "Very Less", "kn": "ತುಂಬಾ ಕಡಿಮೆ", "icon": "☀️"},
        "less": {"en": "Less", "kn": "ಕಡಿಮೆ", "icon": "🌤️"},
        "normal": {"en": "Normal", "kn": "ಸಾಮಾನ್ಯ", "icon": "⛅"},
        "more": {"en": "More", "kn": "ಹೆಚ್ಚು", "icon": "🌧️"},
        "very_more": {"en": "Very More", "kn": "ತುಂಬಾ ಹೆಚ್ಚು", "icon": "⛈️"}
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
