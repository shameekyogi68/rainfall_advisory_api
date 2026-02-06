import pandas as pd
import numpy as np
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import math
import logging

# Import farmer-friendly messages
from farmer_messages import (
    FARMER_MESSAGES,
    get_farmer_friendly_scenario,
    get_rainfall_category_simple,
    get_simple_actions
)

# Setup logging
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
TALUK_BOUNDARIES = Path("taluk_boundaries.json")
RAINFALL_HISTORICAL = Path("rainfall_daily_historical_v1.csv")
WEATHER_DRIVERS = Path("weather_drivers_daily_v1.csv")
MODEL_CLASSIFIER = Path("final_rainfall_classifier_v1.pkl")
FEATURE_SCHEMA = Path("feature_schema_v1.json")

# ==================== CUSTOM EXCEPTIONS ====================
class GPSOutOfBoundsError(Exception):
    """Raised when GPS coordinates are outside Udupi district"""
    pass

class InsufficientDataError(Exception):
    """Raised when there's not enough historical data"""
    pass

class InvalidDateError(Exception):
    """Raised when date is invalid or too far in future/past"""
    pass

# ==================== B1: GPS → TALUK MAPPER ====================
class TalukMapper:
    def __init__(self):
        try:
            with open(TALUK_BOUNDARIES, 'r') as f:
                self.boundaries = json.load(f)
        except FileNotFoundError:
            raise RuntimeError("Taluk boundaries file not found. System configuration error.")
        except json.JSONDecodeError:
            raise RuntimeError("Taluk boundaries file is corrupted.")
    
    def get_taluk(self, lat, lon):
        """
        Maps GPS coordinates to nearest taluk.
        Returns: (taluk_name, confidence)
        Raises: GPSOutOfBoundsError if coordinates are too far from any taluk
        """
        # Validate GPS coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise GPSOutOfBoundsError("Invalid GPS coordinates")
        
        # Check if within Udupi district range
        if not (12.5 <= lat <= 14.5) or not (74.4 <= lon <= 75.3):
            raise GPSOutOfBoundsError(
                "Location outside Udupi district. "
                "This service only works for Udupi district farmers."
            )
        
        # First, check if point is within any bbox
        for taluk_id, data in self.boundaries.items():
            bbox = data['bbox']
            if (bbox['min_lat'] <= lat <= bbox['max_lat'] and 
                bbox['min_lon'] <= lon <= bbox['max_lon']):
                return data['name'].lower(), "high"
        
        # If no bbox match, find nearest taluk center
        min_dist = float('inf')
        nearest_taluk = None
        
        for taluk_id, data in self.boundaries.items():
            center = data['center']
            dist = self._haversine(lat, lon, center['lat'], center['lon'])
            if dist < min_dist:
                min_dist = dist
                nearest_taluk = data['name'].lower()
        
        # Reject if too far (>30km from any taluk center)
        if min_dist > 30:
            raise GPSOutOfBoundsError(
                "Location too far from any known taluk. "
                "Please check your location or contact support."
            )
        
        confidence = "medium" if min_dist < 15 else "low"
        return nearest_taluk, confidence
    
    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        """Calculate distance in km between two GPS points."""
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c

# ==================== B2: FEATURE ENGINEERING ====================
class FeatureEngineer:
    def __init__(self):
        try:
            self.rainfall_df = pd.read_csv(RAINFALL_HISTORICAL)
            self.rainfall_df['date'] = pd.to_datetime(self.rainfall_df['date'], format='mixed')
            self.weather_df = pd.read_csv(WEATHER_DRIVERS)
            self.weather_df['date'] = pd.to_datetime(self.weather_df['date'], format='mixed')
            
            with open(FEATURE_SCHEMA, 'r') as f:
                self.schema = json.load(f)
        except FileNotFoundError as e:
            raise RuntimeError(f"Required data file not found: {e.filename}")
        except Exception as e:
            raise RuntimeError(f"Error loading data files: {str(e)}")
    
    def compute_features(self, taluk, reference_date):
        """
        Compute ML features for a given taluk and date.
        
        B5: TEMPORAL VALIDATION - Only uses data BEFORE reference_date
        """
        try:
            ref_dt = pd.to_datetime(reference_date)
        except:
            raise InvalidDateError("Invalid date format. Use YYYY-MM-DD format.")
        
        # Validate date range
        today = datetime.now()
        if ref_dt > today + timedelta(days=30):
            raise InvalidDateError("Date too far in future (max 30 days ahead)")
        if ref_dt < today - timedelta(days=3650):
            raise InvalidDateError("Date too far in past (max 10 years back)")
        
        # B5: Filter rainfall data strictly before reference date
        rain_data = self.rainfall_df[
            (self.rainfall_df['taluk'] == taluk) &
            (self.rainfall_df['date'] < ref_dt)
        ].sort_values('date')
        
        if len(rain_data) < 30:
            raise InsufficientDataError(
                f"Not enough historical data for {taluk}. "
                "Need at least 30 days of past data."
            )
        
        # Compute lag features
        last_30_days = rain_data.tail(30)
        
        rain_lag_7 = last_30_days.iloc[-7]['rainfall']
        rain_lag_30 = last_30_days.iloc[0]['rainfall']
        rolling_30_rain = last_30_days['rainfall'].sum()
        
        # NEW: Drought-specific features
        rolling_60_rain = rain_data.tail(60)['rainfall'].sum() if len(rain_data) >= 60 else rain_data['rainfall'].sum()
        rolling_90_rain = rain_data.tail(90)['rainfall'].sum() if len(rain_data) >= 90 else rain_data['rainfall'].sum()
        dry_days_count = (last_30_days['rainfall'] < 2).sum()  # Days with < 2mm rain
        
        # Calculate deficit vs historical average for this month
        hist_same_month = self.rainfall_df[
            (self.rainfall_df['taluk'] == taluk) &
            (self.rainfall_df['date'].dt.month == ref_dt.month) &
            (self.rainfall_df['date'].dt.year < ref_dt.year)
        ]
        if len(hist_same_month) > 0:
            avg_monthly = hist_same_month.groupby(hist_same_month['date'].dt.year)['rainfall'].sum().mean()
            rain_deficit = rolling_30_rain - (avg_monthly / 30 * 30)  # Deficit from normal
        else:
            rain_deficit = 0
        
        # Get weather data for reference date (or closest before)
        weather_data = self.weather_df[
            (self.weather_df['taluk'] == taluk) &
            (self.weather_df['date'] <= ref_dt)
        ].sort_values('date')
        
        if len(weather_data) == 0:
            raise InsufficientDataError(
                f"No weather data available for {taluk}"
            )
        
        latest_weather = weather_data.iloc[-1]
        
        # Build feature dict (12 features total)
        features = {
            'rain_lag_7': float(rain_lag_7),
            'rain_lag_30': float(rain_lag_30),
            'rolling_30_rain': float(rolling_30_rain),
            'rolling_60_rain': float(rolling_60_rain),  # NEW
            'rolling_90_rain': float(rolling_90_rain),  # NEW
            'dry_days_count': int(dry_days_count),      # NEW
            'rain_deficit': float(rain_deficit),        # NEW
            'temp': float(latest_weather['temp']),
            'humidity': float(latest_weather['humidity']),
            'wind': float(latest_weather['wind']),
            'pressure': float(latest_weather['pressure']),
            'month': int(ref_dt.month)
        }
        
        # B8: Validate against schema
        expected_features = self.schema['features']
        if set(features.keys()) != set(expected_features):
            raise ValueError(f"Feature computation error")
        
        # Check for NaN/Inf
        for key, val in features.items():
            if pd.isna(val) or np.isinf(val):
                raise ValueError(f"Invalid data detected in {key}")
        
        return features

# ==================== B3: ML INFERENCE ====================
class RainfallPredictor:
    def __init__(self):
        try:
            with open(MODEL_CLASSIFIER, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(FEATURE_SCHEMA, 'r') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            raise RuntimeError("ML model file not found")
        except Exception as e:
            raise RuntimeError(f"Error loading ML model: {str(e)}")
    
    def predict(self, features_dict):
        """
        Run ML inference.
        Returns: (category, confidence_dict)
        """
        try:
            # Ensure correct feature order
            feature_order = self.schema['features']
            X = np.array([[features_dict[f] for f in feature_order]])
            
            # Get prediction
            category = self.model.predict(X)[0]
            
            # B10: Get probability distribution
            probabilities = self.model.predict_proba(X)[0]
            class_names = self.model.classes_
            
            confidence_dict = {
                cls: float(prob) for cls, prob in zip(class_names, probabilities)
            }
            
            return category, confidence_dict
        except Exception as e:
            raise RuntimeError(f"ML prediction error: {str(e)}")

# ==================== B6: LIVE WEATHER ====================
def get_live_forecast_safe(lat, lon):
    """
    Enhanced version with proper error handling.
    Returns: (rainfall_mm, status, error_message)
    """
    import requests
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "timezone": "auto",
        "forecast_days": 7
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily_rain = data.get("daily", {}).get("precipitation_sum", [])
        if not daily_rain:
            return None, "error", "Weather service returned no data"
        
        total_rain_7d = sum([x for x in daily_rain if x is not None])
        
        return total_rain_7d, "success", None
        
    except requests.Timeout:
        return None, "error", "Weather service timeout"
    except requests.RequestException as e:
        return None, "error", f"Weather service unavailable"
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None, "error", "Weather data processing error"

# ==================== FARMER-FRIENDLY OUTPUT BUILDER ====================
def build_farmer_response(ml_category, forecast_7day_mm, taluk, geo_confidence, confidences):
    """
    Build farmer-friendly response with translation support
    """
    # Get scenario
    scenario_key = get_farmer_friendly_scenario(ml_category, forecast_7day_mm if forecast_7day_mm else 10.0)
    scenario = FARMER_MESSAGES['scenarios'][scenario_key]
    
    # Get simple rainfall category
    rainfall_category = get_rainfall_category_simple(forecast_7day_mm if forecast_7day_mm else 10.0)
    rainfall_info = FARMER_MESSAGES['measurements'][rainfall_category]
    
    # Get actions
    action_keys = get_simple_actions(scenario_key)
    actions = [FARMER_MESSAGES['actions'][key] for key in action_keys]
    
    # Build response
    return {
        "status": "success",
        
        # Location (simple)
        "location": {
            "area": taluk.capitalize(),
            "district": {
                "en": "Udupi District",
                "kn": "ಉಡುಪಿ ಜಿಲ್ಲೆ"
            },
            "accuracy": geo_confidence
        },
        
        # Main status (large, visual)
        "main_status": {
            "title": scenario['title'],
            "message": scenario['message'],
            "icon": scenario['title']['icon'],
            "priority": scenario['priority'],
            "color": FARMER_MESSAGES['alert_levels'][scenario['priority'].lower()]['color']
        },
        
        # Rainfall info (simple numbers)
        "rainfall": {
            "next_7_days": {
                "amount_mm": forecast_7day_mm if forecast_7day_mm else None,
                "category": rainfall_info,
                "simple_description": {
                    "en": f"{rainfall_info['en']} rain in next 7 days",
                    "kn": f"ಮುಂದಿನ 7 ದಿನದಲ್ಲಿ {rainfall_info['kn']} ಮಳೆ"
                }
            },
            "monthly_prediction": {
                "category": ml_category,
                "confidence_percent": int(confidences.get(ml_category, 0) * 100)
            }
        },
        
        # What to do (clear actions)
        "what_to_do": {
            "title": {
                "en": "What You Should Do",
                "kn": "ನೀವು ಏನು ಮಾಡಬೇಕು"
            },
            "actions": actions,
            "priority_level": scenario['priority']
        },
        
        # Technical details (for advanced users/app developers)
        "technical_details": {
            "ml_prediction": ml_category,
            "confidence_scores": confidences,
            "model_version": "v1",
            "forecast_available": forecast_7day_mm is not None
        }
    }

# ==================== ERROR RESPONSE BUILDER ====================
def build_error_response(error_type, error_message, user_friendly=True):
    """
    Build user-friendly error responses
    """
    error_messages = {
        "gps_error": {
            "title": {
                "en": "Location Problem",
                "kn": "ಸ್ಥಳ ಸಮಸ್ಯೆ"
            },
            "message": {
                "en": "We cannot find your location. Please check if you are in Udupi district.",
                "kn": "ನಿಮ್ಮ ಸ್ಥಳ ಹುಡುಕಲು ಆಗುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ನೀವು ಉಡುಪಿ ಜಿಲ್ಲೆಯಲ್ಲಿದ್ದೀರಾ ಎಂದು ಪರೀಕ್ಷಿಸಿ."
            },
            "icon": "📍",
            "action": {
                "en": "Turn on GPS and try again",
                "kn": "GPS ಆನ್ ಮಾಡಿ ಮತ್ತು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ"
            }
        },
        "data_error": {
            "title": {
                "en": "Not Enough Information",
                "kn": "ಸಾಕಷ್ಟು ಮಾಹಿತಿ ಇಲ್ಲ"
            },
            "message": {
                "en": "We don't have enough data for your area yet.",
                "kn": "ನಿಮ್ಮ ಪ್ರದೇಶಕ್ಕೆ ಇನ್ನೂ ಸಾಕಷ್ಟು ಡೇಟಾ ಇಲ್ಲ."
            },
            "icon": "📊",
            "action": {
                "en": "Please contact support",
                "kn": "ದಯವಿಟ್ಟು ಸಹಾಯ ಕೇಂದ್ರವನ್ನು ಸಂಪರ್ಕಿಸಿ"
            }
        },
        "date_error": {
            "title": {
                "en": "Date Problem",
                "kn": "ದಿನಾಂಕ ಸಮಸ್ಯೆ"
            },
            "message": {
                "en": "The date you selected is not valid.",
                "kn": "ನೀವು ಆರಿಸಿದ ದಿನಾಂಕ ಮಾನ್ಯವಾಗಿಲ್ಲ."
            },
            "icon": "📅",
            "action": {
                "en": "Select a date within next 30 days",
                "kn": "ಮುಂದಿನ 30 ದಿನಗಳಲ್ಲಿ ದಿನಾಂಕ ಆರಿಸಿ"
            }
        },
        "system_error": {
            "title": {
                "en": "System Problem",
                "kn": "ಸಿಸ್ಟಮ್ ಸಮಸ್ಯೆ"
            },
            "message": {
                "en": "Something went wrong. Please try again.",
                "kn": "ಏನೋ ತಪ್ಪಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
            },
            "icon": "⚙️",
            "action": {
                "en": "Try again in a few minutes",
                "kn": "ಕೆಲವು ನಿಮಿಷಗಳಲ್ಲಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ"
            }
        }
    }
    
    error_info = error_messages.get(error_type, error_messages["system_error"])
    
    return {
        "status": "error",
        "error": {
            "type": error_type,
            "title": error_info["title"],
            "message": error_info["message"],
            "icon": error_info["icon"],
            "what_to_do": error_info["action"],
            "technical_message": error_message if not user_friendly else None
        }
    }

# ==================== B4: MAIN API LOGIC ====================
def process_advisory_request(user_id, gps_lat, gps_long, date_str):
    """
    Main backend pipeline: GPS → Features → ML → Farmer-Friendly Output
    With comprehensive error handling
    """
    try:
        # Step 1: GPS → Taluk (B1)
        try:
            mapper = TalukMapper()
            taluk, geo_confidence = mapper.get_taluk(gps_lat, gps_long)
        except GPSOutOfBoundsError as e:
            return build_error_response("gps_error", str(e))
        
        # Step 2: Compute Features (B2 + B5)
        try:
            engineer = FeatureEngineer()
            features = engineer.compute_features(taluk, date_str)
        except InvalidDateError as e:
            return build_error_response("date_error", str(e))
        except InsufficientDataError as e:
            return build_error_response("data_error", str(e))
        
        # Step 3: ML Prediction (B3)
        try:
            predictor = RainfallPredictor()
            ml_category, confidences = predictor.predict(features)
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return build_error_response("system_error", "Prediction system error")
        
        # Step 4: Live Weather (B6)
        live_rain, weather_status, weather_error = get_live_forecast_safe(gps_lat, gps_long)
        
        # If weather API fails, use conservative fallback
        if weather_status == "error":
            logger.warning(f"Weather API failed: {weather_error}")
            # Use historical average as safe fallback
            live_rain = features.get('rolling_30_rain', 10.0) / 4  # Approximate weekly
        
        # Step 5: Build Farmer-Friendly Response
        response = build_farmer_response(
            ml_category=ml_category,
            forecast_7day_mm=live_rain,
            taluk=taluk,
            geo_confidence=geo_confidence,
            confidences=confidences
        )
        
        # Add weather data source info
        response['data_sources'] = {
            "weather_forecast": "live" if weather_status == "success" else "historical_estimate",
            "location_accuracy": geo_confidence,
            "last_updated": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in advisory request: {e}", exc_info=True)
        return build_error_response("system_error", str(e), user_friendly=True)

# ==================== TESTING ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FARMER-FRIENDLY BACKEND TEST")
    print("=" * 60)
    
    # Test Case: Farmer in Udupi
    test_request = {
        "user_id": "farmer_123",
        "gps_lat": 13.3409,
        "gps_long": 74.7421,
        "date": "2025-06-15"
    }
    
    print(f"\n📥 REQUEST:")
    print(json.dumps(test_request, indent=2))
    
    result = process_advisory_request(
        test_request['user_id'],
        test_request['gps_lat'],
        test_request['gps_long'],
        test_request['date']
    )
    
    print(f"\n📤 FARMER-FRIENDLY RESPONSE:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
