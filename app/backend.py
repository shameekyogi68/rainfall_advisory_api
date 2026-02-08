import os
import pandas as pd
import numpy as np
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import math
import logging

# Import farmer-friendly messages
from app.core.messages import (
    FARMER_MESSAGES,
    get_farmer_friendly_scenario,
    get_rainfall_category_simple,
    get_rainfall_category_simple,
    get_simple_actions
)

from app.core.uncertainty import UncertaintyQuantifier
from app.config import settings

# Setup logging
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
TALUK_BOUNDARIES = settings.BASE_DIR / "data/taluk_boundaries.json"
RAINFALL_HISTORICAL = settings.RAINFALL_DATA_PATH
WEATHER_DRIVERS = settings.WEATHER_DATA_PATH
MODEL_CLASSIFIER = settings.DISTRICT_MODEL_PATH
FEATURE_SCHEMA = settings.FEATURE_SCHEMA_PATH

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
    _instance = None
    _use_db = False
    _engine = None
    _rainfall_df = None
    _weather_df = None
    _schema = None
    
    def __new__(cls, db_url=None):
        """Singleton pattern: only create one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_data(db_url)
        return cls._instance
    
    @classmethod
    def _load_data(cls, db_url=None):
        """Load data once and cache in memory"""
        if cls._rainfall_df is not None or cls._use_db:
            return  # Already loaded
        
        # Try Database Connection first
        import getpass
        default_user = getpass.getuser()
        db_url = db_url or os.getenv("DATABASE_URL", f"postgresql://{default_user}@localhost:5432/rainfall_db")
        if db_url:
            try:
                from sqlalchemy import create_engine, text
                cls._engine = create_engine(db_url)
                # Test connection
                with cls._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                cls._use_db = True
                logger.info("✅ FeatureEngineer connected to Database")
            except Exception as e:
                logger.warning(f"⚠️ Database connection failed: {e}. Falling back to CSVs.")
        
        # Fallback to CSVs
        if not cls._use_db:
            try:
                logger.info("Loading CSV data (first time)...")
                cls._rainfall_df = pd.read_csv(RAINFALL_HISTORICAL)
                cls._rainfall_df['date'] = pd.to_datetime(cls._rainfall_df['date'], format='mixed')
                cls._weather_df = pd.read_csv(WEATHER_DRIVERS)
                cls._weather_df['date'] = pd.to_datetime(cls._weather_df['date'], format='mixed')
                logger.info("✅ FeatureEngineer loaded and cached CSV data")
            except FileNotFoundError as e:
                raise RuntimeError(f"Required data file not found: {e.filename}")
            except Exception as e:
                raise RuntimeError(f"Error loading data files: {str(e)}")
            
        try:
            with open(FEATURE_SCHEMA, 'r') as f:
                cls._schema = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Error loading schema: {str(e)}")
    
    @property
    def use_db(self):
        return self._use_db
    
    @property
    def engine(self):
        return self._engine
    
    @property
    def rainfall_df(self):
        return self._rainfall_df
    
    @property
    def weather_df(self):
        return self._weather_df
    
    @property
    def schema(self):
        return self._schema

    def _get_rainfall_data(self, taluk, ref_dt):
        """Fetch rainfall data (historical) for feature computation"""
        if self.use_db:
            query = f"""
                SELECT date, rainfall_mm as rainfall 
                FROM rainfall_history 
                WHERE taluk = '{taluk}' AND date < '{ref_dt.strftime('%Y-%m-%d')}'
                ORDER BY date ASC
            """
            df = pd.read_sql(query, self.engine)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            return df
        else:
            return self.rainfall_df[
                (self.rainfall_df['taluk'] == taluk) &
                (self.rainfall_df['date'] < ref_dt)
            ].sort_values('date')

    def _get_weather_data(self, taluk, ref_dt):
        """Fetch weather driver data"""
        if self.use_db:
            query = f"""
                SELECT date, temp, humidity, wind, pressure
                FROM weather_drivers
                WHERE taluk = '{taluk}' AND date <= '{ref_dt.strftime('%Y-%m-%d')}'
                ORDER BY date ASC
            """
            df = pd.read_sql(query, self.engine)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            return df
        else:
            return self.weather_df[
                (self.weather_df['taluk'] == taluk) &
                (self.weather_df['date'] <= ref_dt)
            ].sort_values('date')

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
        
        # B5: Fetch Data (DB or CSV via helper)
        rain_data = self._get_rainfall_data(taluk, ref_dt)
        
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
        # For historical average, we need aggregation across years
        if self.use_db:
            # Efficient SQL aggregation
            month = ref_dt.month
            query = f"""
                SELECT EXTRACT(YEAR FROM date) as year, SUM(rainfall_mm) as monthly_rain
                FROM rainfall_history
                WHERE taluk = '{taluk}' 
                AND EXTRACT(MONTH FROM date) = {month}
                AND date < '{ref_dt.strftime('%Y-%m-%d')}'
                GROUP BY year
            """
            hist_stats = pd.read_sql(query, self.engine)
            avg_monthly = hist_stats['monthly_rain'].mean() if not hist_stats.empty else 0
        else:
            hist_same_month = self.rainfall_df[
                (self.rainfall_df['taluk'] == taluk) &
                (self.rainfall_df['date'].dt.month == ref_dt.month) &
                (self.rainfall_df['date'].dt.year < ref_dt.year)
            ]
            if len(hist_same_month) > 0:
                avg_monthly = hist_same_month.groupby(hist_same_month['date'].dt.year)['rainfall'].sum().mean()
            else:
                avg_monthly = 0

        rain_deficit = rolling_30_rain - (avg_monthly if avg_monthly else 0)
        
        # Get weather data
        weather_data = self._get_weather_data(taluk, ref_dt)
        
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
            'rolling_60_rain': float(rolling_60_rain),
            'rolling_90_rain': float(rolling_90_rain),
            'dry_days_count': int(dry_days_count),
            'rain_deficit': float(rain_deficit),
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
    _instance = None
    _model = None
    _schema = None
    _quantifier = None
    
    def __new__(cls):
        """Singleton pattern: only create one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_model()
        return cls._instance
    
    @classmethod
    def _load_model(cls):
        """Load model once and cache in memory"""
        if cls._model is not None:
            return  # Already loaded
            
        try:
            logger.info("Loading ML model (first time)...")
            with open(MODEL_CLASSIFIER, 'rb') as f:
                cls._model = pickle.load(f)
            
            with open(FEATURE_SCHEMA, 'r') as f:
                cls._schema = json.load(f)
                
            # Initialize UncertaintyQuantifier
            try:
                cls._quantifier = UncertaintyQuantifier(
                    model_path=str(MODEL_CLASSIFIER),
                    taluk_models_path=str(settings.TALUK_MODELS_PATH)
                )
            except Exception as e:
                logger.warning(f"UncertaintyQuantifier failed to init: {e}")
                cls._quantifier = None
            
            logger.info("✅ ML model loaded and cached")
                
        except FileNotFoundError:
            raise RuntimeError("ML model file not found")
        except Exception as e:
            raise RuntimeError(f"Error loading ML model: {str(e)}")
    
    @property
    def model(self):
        return self._model
    
    @property
    def schema(self):
        return self._schema
    
    @property
    def quantifier(self):
        return self._quantifier
    
    def predict(self, features_dict, taluk=None):
        """
        Run ML inference with Uncertainty Quantification.
        Returns: (category, confidence_dict, uncertainty_data)
        """
        try:
            # Ensure correct feature order
            feature_order = self.schema['features']
            features_list = [features_dict[f] for f in feature_order]
            
            if self.quantifier:
                # Use UncertaintyQuantifier logic
                result = self.quantifier.get_prediction_with_uncertainty(features_list, taluk)
                
                category = result['prediction']['category']
                
                # Convert percentages back to 0-1 probabilities for consistency
                probs = result['prediction']['probabilities']
                confidence_dict = {
                    'Deficit': probs['deficit'] / 100.0,
                    'Normal': probs['normal'] / 100.0,
                    'Excess': probs['excess'] / 100.0
                }
                
                return category, confidence_dict, result
                
            else:
                # Fallback to simple prediction
                X = np.array([features_list])
                
                # Get raw probabilities
                probabilities = self.model.predict_proba(X)[0]
                class_names = self.model.classes_
                
                raw_conf = {
                    cls: float(prob) for cls, prob in zip(class_names, probabilities)
                }
                
                # Apply Probability Calibration (The "Correction" Layer)
                return category, confidence_dict, None

        except Exception as e:
            raise RuntimeError(f"ML prediction error: {str(e)}")

    def calibrate_prediction(self, raw_conf):
        """
        Calibrates raw ML probabilities to fix "Normal" bias.
        Penalizes 'Normal' and boosts 'Deficit'/'Excess' if signal exists.
        """
        calibrated = raw_conf.copy()
        
        # 1. Penalize 'Normal' (it's often over-predicted due to class imbalance)
        if calibrated.get('Normal', 0) > 0.4:
            calibrated['Normal'] *= 0.8  # 20% penalty
            
        # 2. Boost Extremes (if they have non-trivial probability)
        for extreme in ['Deficit', 'Excess']:
             if calibrated.get(extreme, 0) > 0.25:
                 calibrated[extreme] *= 1.3  # 30% boost
        
        # 3. Renormalize to sum to 1.0
        total = sum(calibrated.values())
        for k in calibrated:
            calibrated[k] /= total
            
        # 4. Determine new winner
        # If 'Normal' is winner but margin is small (<10%), prefer extreme
        # (Risk-averse strategy: better to warn than miss)
        sorted_cats = sorted(calibrated.items(), key=lambda x: x[1], reverse=True)
        winner = sorted_cats[0][0]
        score = sorted_cats[0][1]
        
        if winner == 'Normal' and score < 0.5:
            # Check if an extreme is close second
            second = sorted_cats[1]
            if second[0] in ['Deficit', 'Excess'] and (score - second[1]) < 0.1:
                winner = second[0]
                # Swap probabilities to reflect this override
                calibrated[winner], calibrated['Normal'] = calibrated['Normal'], calibrated[winner]
        
        return winner, calibrated

# ==================== B6: LIVE WEATHER ====================
def get_live_forecast_safe(lat, lon):
    """
    Enhanced version with HOURLY precision for Flash Flood Detection.
    Returns: (rainfall_mm_7d, max_intensity_mm_hr, status, error_message)
    """
    import requests
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "hourly": "precipitation", # NEW: High-res data
        "timezone": "auto",
        "forecast_days": 7
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 1. Daily Totals (Volume)
        daily_rain = data.get("daily", {}).get("precipitation_sum", [])
        if not daily_rain:
            return None, None, "error", "Weather service returned no data"
        
        total_rain_7d = sum([x for x in daily_rain if x is not None])
        
        # 2. Hourly Intensity (Flash Flood Risk)
        hourly_rain = data.get("hourly", {}).get("precipitation", [])
        max_intensity = 0.0
        if hourly_rain:
            # Filter None values and find max
            valid_hourly = [x for x in hourly_rain if x is not None]
            if valid_hourly:
                max_intensity = max(valid_hourly)
        
        return total_rain_7d, max_intensity, "success", None
        
    except requests.Timeout:
        return None, None, "error", "Weather service timeout"
    except requests.RequestException as e:
        return None, None, "error", "Weather service unavailable"
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None, None, "error", "Weather data processing error"

# ==================== FARMER-FRIENDLY OUTPUT BUILDER ====================
# ==================== FARMER-FRIENDLY OUTPUT BUILDER ====================
def build_farmer_response(ml_category, forecast_7day_mm, taluk, geo_confidence, confidences, uncertainty_data=None, max_intensity_mm_per_hr=0.0, **kwargs):
    """
    Constructs the final response using:
    1. ML Category (from calibrated probs)
    2. ML Confidence (from calibrated probs)
    3. Live Forecast Overlay (Volume + Intensity)
    """
    # Alias confidences for backward compatibility if needed
    confidence_dict = confidences
    from app.core.rules import generate_alert
    
    # INTENSITY CHECK (Local Logic for Flash Flood)
    # INTENSITY CHECK (Local Logic for Flash Flood)
    if max_intensity_mm_per_hr > 15.0:
        # Flash Flood Override
        alert = {
            "status": "DANGER",
            "severity": "CRITICAL",
            "type": "FLASH_FLOOD",
            "sms_text": {
                "en": "CRITICAL: Flash Flood Risk (>15mm/hr). Drain fields immediately. Stop fertilizer application.",
                "kn": "ತುರ್ತು: ದಿಢೀರ್ ಪ್ರವಾಹ ಸಾಧ್ಯತೆ (>15mm/hr). ಕೂಡಲೇ ನೀರು ಹೊರಹಾಕಿ. ಗೊಬ್ಬರ ಹಾಕಬೇಡಿ."
            },
            "whatsapp_text": {
                "en": "🚨 *CROP DANGER: FLASH FLOOD*\n\nIntense rainfall (>15mm/hr) detected.\n\n*Action Required:*\n- Open all drainage channels\n- Postpone fertilizer/chemical spraying\n- Protect harvested crops",
                "kn": "🚨 *ಬೆಳೆ ಅಪಾಯ: ದಿಢೀರ್ ಪ್ರವಾಹ*\n\nಭಾರೀ ಮಳೆ (>15mm/hr) ಪತ್ತೆಯಾಗಿದೆ.\n\n*ತುರ್ತು ಕ್ರಮಗಳು:*\n- ಎಲ್ಲಾ ಕಾಲುವೆಗಳನ್ನು ತೆರೆಯಿರಿ\n- ಗೊಬ್ಬರ/ಔಷಧಿ ಸಿಂಪಡಣೆ ಮುಂದೂಡಿ\n- ಕಟಾವು ಮಾಡಿದ ಬೆಳೆ ರಕ್ಷಿಸಿ"
            }
        }
    else:
        # Standard Rules
        # Note: generate_alert now expects 'confidences' instead of 'ml_rainfall_mm'
        alert = generate_alert(ml_category, confidences, forecast_7day_mm)

    # Instantiate advisory for detailed recommendations
    from app.core.advisory import AdvisoryService
    advisory_service = AdvisoryService()
    
    # Get detailed advice
    risk_level, risk_icon, risk_msg = advisory_service.get_risk_level(ml_category, confidences.get(ml_category, 0)*100)
    
    # Get actions based on category
    if ml_category == 'Excess':
        detailed_actions = advisory_service.get_actions_for_excess(confidences.get('Excess', 0)*100)
    elif ml_category == 'Deficit':
        detailed_actions = advisory_service.get_actions_for_deficit(confidences.get('Deficit', 0)*100)
    else:
        detailed_actions = advisory_service.get_actions_for_normal()

    return {
        "status": "success",
        
        # Main status (large, visual)
        "main_status": {
            "title": {
                "en": alert['type'].replace("_", " "),
                "kn": {
                    "FLOOD": "ಪ್ರವಾಹ",
                    "DROUGHT": "ಬರಗಾಲ",
                    "NORMAL": "ಸಾಧಾರಣ",
                    "WET_NORMAL": "ತೇವಭರಿತ",
                    "DROUGHT_RELIEF": "ಬರ ಪರಿಹಾರ",
                    "FLASH_FLOOD": "ದಿಢೀರ್ ಪ್ರವಾಹ",
                    "HIGH_TEMPERATURE": "ಹೆಚ್ಚಿನ ಉಷ್ಣಾಂಶ",
                    "COLD_WEATHER": "ಶೀತ ಹವಾಮಾನ",
                    "HEAVY_RAIN": "ಭಾರೀ ಮಳೆ",
                    "MODERATE_RAIN": "ಸಾಧಾರಣ ಮಳೆ"
                }.get(alert['type'], alert['type'])
            },
            "message": alert['sms_text'], # Now a dictionary {en, kn}
            "icon": "🚨" if alert['severity'] in ['HIGH', 'CRITICAL'] else "🟢",
            "priority": alert['severity'],
            "color": "#D32F2F" if alert['severity'] in ['HIGH', 'CRITICAL'] else "#4CAF50"
        },
        
        # Rainfall info (simple numbers)
        "rainfall": {
            "next_7_days": {
                "amount_mm": round(forecast_7day_mm, 1) if forecast_7day_mm else 0.0,
                "max_intensity": round(max_intensity_mm_per_hr, 1),
                "category": ml_category
            },
            "monthly_prediction": {
                "category": ml_category,
                "confidence_percent": int(confidences.get(ml_category, 0) * 100)
            }
        },
        
        # What to do (clear actions)
        "what_to_do": {
            "title": {
                "en": "Advisory",
                "kn": "ಸಲಹೆ"
            },
            "whatsapp_summary": alert['whatsapp_text'], # Now a dictionary {en, kn}
            "actions": detailed_actions, # detailed structured actions
            "priority_level": alert['severity']
        },
        
        # Technical details (for advanced users/app developers)
        "technical_details": {
            "ml_prediction": ml_category,
            "confidence_scores": confidences,
            "model_version": "v2_calibrated",
            "forecast_available": forecast_7day_mm is not None,
            "uncertainty_analysis": uncertainty_data.get('uncertainty') if uncertainty_data else None,
            "prediction_intervals": uncertainty_data.get('prediction_intervals') if uncertainty_data else None
        },
        
        # Location info (Required by main.py logging)
        "location": {
            "taluk": taluk,
            "district": "Udupi",
            "confidence": geo_confidence
        }
    }

# ==================== ERROR RESPONSE BUILDER ====================
def build_error_response(error_type, error_message, user_friendly=True):
    """
    Build user-friendly error responses with refined translations
    """
    error_messages = {
        "gps_error": {
            "title": {
                "en": "Location Problem",
                "kn": "ಸ್ಥಳ ಪತ್ತೆ ಸಮಸ್ಯೆ"
            },
            "message": {
                "en": "We cannot find your location. Please check if you are in Udupi district.",
                "kn": "ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಪತ್ತೆಹಚ್ಚಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ. ನೀವು ಉಡುಪಿ ಜಿಲ್ಲೆಯಲ್ಲಿದ್ದೀರಾ ಎಂದು ಪರಿಶೀಲಿಸಿ."
            },
            "icon": "📍",
            "action": {
                "en": "Turn on GPS and try again",
                "kn": "GPS ಆನ್ ಮಾಡಿ ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ"
            }
        },
        "data_error": {
            "title": {
                "en": "Data Not Available",
                "kn": "ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ"
            },
            "message": {
                "en": "We don't have enough rainfall data for your area yet.",
                "kn": "ನಿಮ್ಮ ಪ್ರದೇಶದ ಮಳೆಯ ಮಾಹಿತಿಯು ಸದ್ಯಕ್ಕೆ ನಮ್ಮ ಬಳಿ ಇಲ್ಲ."
            },
            "icon": "📊",
            "action": {
                "en": "Contact Support",
                "kn": "ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ"
            }
        },
        "date_error": {
            "title": {
                "en": "Invalid Date",
                "kn": "ದಿನಾಂಕ ತಪ್ಪಾಗಿದೆ"
            },
            "message": {
                "en": "The date you selected is not valid.",
                "kn": "ನೀವು ಆಯ್ಕೆ ಮಾಡಿದ ದಿನಾಂಕ ಸರಿಯಿಲ್ಲ."
            },
            "icon": "📅",
            "action": {
                "en": "Select a valid date",
                "kn": "ಸರಿಯಾದ ದಿನಾಂಕವನ್ನು ಆರಿಸಿ"
            }
        },
        "system_error": {
            "title": {
                "en": "System Error",
                "kn": "ತಾಂತ್ರಿಕ ದೋಷ"
            },
            "message": {
                "en": "Something went wrong. Please try again later.",
                "kn": "ಏನೋ ತಪ್ಪಾಗಿದೆ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ."
            },
            "icon": "⚙️",
            "action": {
                "en": "Try again",
                "kn": "ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ"
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
def process_advisory_request(user_id, gps_lat, gps_long, date_str, mapper=None, engineer=None, predictor=None):
    """
    Main backend pipeline: GPS → Features → ML → Farmer-Friendly Output
    With comprehensive error handling and Dependency Injection for performance
    """
    try:
        # Step 1: GPS → Taluk (B1)
        try:
            if mapper is None:
                mapper = TalukMapper()
            taluk, geo_confidence = mapper.get_taluk(gps_lat, gps_long)
        except GPSOutOfBoundsError as e:
            return build_error_response("gps_error", str(e))
        
        # Step 2: Compute Features (B2 + B5)
        try:
            if engineer is None:
                engineer = FeatureEngineer()
            features = engineer.compute_features(taluk, date_str)
        except InvalidDateError as e:
            return build_error_response("date_error", str(e))
        except InsufficientDataError as e:
            return build_error_response("data_error", str(e))
        
        # Step 3: ML Prediction (B3)
        try:
            if predictor is None:
                predictor = RainfallPredictor()
            ml_category, confidences, uncertainty_data = predictor.predict(features, taluk)
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return build_error_response("system_error", "Prediction system error")
        
        # Step 4: Live Weather (B6)
        live_rain, max_intensity, weather_status, weather_error = get_live_forecast_safe(gps_lat, gps_long)
        
        # If weather API fails, use conservative fallback
        if weather_status == "error":
            logger.warning(f"Weather API failed: {weather_error}. Using climatological mean.")
            # Use historical average for that month (rough estimate)
            # Better safe than sorry: Assume "Normal" rainfall (~5-10mm/day in monsoon)
            live_rain = 50.0 # Conservative estimate (moderate rain) to avoid missing potential wetness
            max_intensity = 0.0 # Cannot guess intensity without data
            weather_status = "estimated"
        
        # Step 5: Build Farmer-Friendly Response
        response = build_farmer_response(
            ml_category=ml_category,
            forecast_7day_mm=live_rain,
            taluk=taluk,
            geo_confidence=geo_confidence,
            confidences=confidences,
            uncertainty_data=uncertainty_data,
            max_intensity_mm_per_hr=max_intensity # Added max_intensity
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
