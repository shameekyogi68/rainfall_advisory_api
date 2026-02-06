import pandas as pd
import numpy as np
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import math

# ==================== CONFIGURATION ====================
TALUK_BOUNDARIES = Path("taluk_boundaries.json")
RAINFALL_HISTORICAL = Path("rainfall_daily_historical_v1.csv")
WEATHER_DRIVERS = Path("weather_drivers_daily_v1.csv")
MODEL_CLASSIFIER = Path("final_rainfall_classifier_v1.pkl")
FEATURE_SCHEMA = Path("feature_schema_v1.json")

# ==================== B1: GPS → TALUK MAPPER ====================
class TalukMapper:
    def __init__(self):
        with open(TALUK_BOUNDARIES, 'r') as f:
            self.boundaries = json.load(f)
    
    def get_taluk(self, lat, lon):
        """
        Maps GPS coordinates to nearest taluk.
        Returns: (taluk_name, confidence)
        """
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
        
        confidence = "medium" if min_dist < 15 else "low"  # 15km threshold
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
        self.rainfall_df = pd.read_csv(RAINFALL_HISTORICAL)
        self.rainfall_df['date'] = pd.to_datetime(self.rainfall_df['date'])
        self.weather_df = pd.read_csv(WEATHER_DRIVERS)
        self.weather_df['date'] = pd.to_datetime(self.weather_df['date'])
        
        with open(FEATURE_SCHEMA, 'r') as f:
            self.schema = json.load(f)
    
    def compute_features(self, taluk, reference_date):
        """
        Compute ML features for a given taluk and date.
        
        B5: TEMPORAL VALIDATION - Only uses data BEFORE reference_date
        """
        ref_dt = pd.to_datetime(reference_date)
        
        # B5: Filter rainfall data strictly before reference date
        rain_data = self.rainfall_df[
            (self.rainfall_df['taluk'] == taluk) &
            (self.rainfall_df['date'] < ref_dt)
        ].sort_values('date')
        
        if len(rain_data) < 30:
            raise ValueError(f"Insufficient historical data for {taluk} before {reference_date}")
        
        # Compute lag features
        last_30_days = rain_data.tail(30)
        
        if len(last_30_days) < 30:
            raise ValueError(f"Cannot compute 30-day lags - only {len(last_30_days)} days available")
        
        rain_lag_7 = last_30_days.iloc[-7]['rainfall']
        rain_lag_30 = last_30_days.iloc[0]['rainfall']
        rolling_30_rain = last_30_days['rainfall'].sum()
        
        # Get weather data for reference date (or closest before)
        weather_data = self.weather_df[
            (self.weather_df['taluk'] == taluk) &
            (self.weather_df['date'] <= ref_dt)
        ].sort_values('date')
        
        if len(weather_data) == 0:
            raise ValueError(f"No weather data available for {taluk} up to {reference_date}")
        
        latest_weather = weather_data.iloc[-1]
        
        # Build feature dict
        features = {
            'rain_lag_7': rain_lag_7,
            'rain_lag_30': rain_lag_30,
            'rolling_30_rain': rolling_30_rain,
            'temp': latest_weather['temp'],
            'humidity': latest_weather['humidity'],
            'wind': latest_weather['wind'],
            'pressure': latest_weather['pressure'],
            'month': ref_dt.month
        }
        
        # B8: Validate against schema
        expected_features = self.schema['features']
        if set(features.keys()) != set(expected_features):
            raise ValueError(f"Feature mismatch. Expected: {expected_features}, Got: {list(features.keys())}")
        
        # Check for NaN/Inf
        for key, val in features.items():
            if pd.isna(val) or np.isinf(val):
                raise ValueError(f"Invalid value for feature '{key}': {val}")
        
        return features

# ==================== B3: ML INFERENCE ====================
class RainfallPredictor:
    def __init__(self):
        with open(MODEL_CLASSIFIER, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(FEATURE_SCHEMA, 'r') as f:
            self.schema = json.load(f)
    
    def predict(self, features_dict):
        """
        Run ML inference.
        Returns: (category, confidence_dict)
        """
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

# ==================== B6: FIXED LIVE WEATHER ====================
def get_live_forecast_safe(lat, lon):
    """
    Enhanced version with proper error handling.
    Returns: (rainfall_mm, status)
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
        total_rain_7d = sum([x for x in daily_rain if x is not None])
        
        return total_rain_7d, "success"
        
    except Exception as e:
        print(f"⚠️ Weather API Error: {e}")
        # Return None instead of 0.0 to signal error
        return None, "error"

# ==================== B4: MAIN API LOGIC ====================
def process_advisory_request(user_id, gps_lat, gps_long, date_str):
    """
    Main backend pipeline: GPS → Features → ML → Alert
    """
    from decision_rules import generate_alert
    
    response = {
        "status": "error",
        "message": ""
    }
    
    try:
        # Step 1: GPS → Taluk (B1)
        mapper = TalukMapper()
        taluk, geo_confidence = mapper.get_taluk(gps_lat, gps_long)
        
        # Step 2: Compute Features (B2 + B5)
        engineer = FeatureEngineer()
        features = engineer.compute_features(taluk, date_str)
        
        # Step 3: ML Prediction (B3)
        predictor = RainfallPredictor()
        ml_category, confidences = predictor.predict(features)
        
        # Step 4: Live Weather (B6)
        live_rain, weather_status = get_live_forecast_safe(gps_lat, gps_long)
        
        # Handle weather API failure
        if weather_status == "error":
            # Use historical average as fallback
            live_rain = 10.0  # Conservative fallback (will be improved in B13)
            weather_note = "Using historical estimate (live data unavailable)"
        else:
            weather_note = "Live forecast"
        
        # Step 5: Decision Logic
        alert = generate_alert(ml_category, 100.0, live_rain)
        
        # Step 6: Build Response
        response = {
            "status": "success",
            "location": {
                "taluk": taluk.capitalize(),
                "district": "Udupi",
                "confidence": geo_confidence
            },
            "prediction": {
                "month_status": ml_category,
                "confidence": confidences,
                "ml_model_version": "v1"
            },
            "alert": {
                "show_alert": alert['severity'] in ['HIGH', 'CRITICAL'],
                "level": alert['severity'],
                "type": alert['type'],
                "title": alert['whatsapp_text'].split('\\n')[0],
                "message": alert['sms_text'],
                "action_card": {
                    "header": "Recommended Action",
                    "body": alert['whatsapp_text']
                }
            },
            "weather_summary": {
                "forecast_7day_total": f"{live_rain} mm" if live_rain else "Unavailable",
                "condition": weather_note
            }
        }
        
    except Exception as e:
        response = {
            "status": "error",
            "message": str(e),
            "code": "PROCESSING_ERROR"
        }
    
    return response

# ==================== TESTING ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 PRODUCTION BACKEND TEST")
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
    
    print(f"\n📤 RESPONSE:")
    print(json.dumps(result, indent=2))
