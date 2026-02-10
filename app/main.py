from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import json
import os
from pathlib import Path
from app.config import settings

# Base directory for resolving paths
# BASE_DIR is now available in settings

from app.backend import process_advisory_request, TalukMapper, FeatureEngineer, RainfallPredictor
from app.core.advisory import AdvisoryService

# ... (logging setup remains same) ...

# ==================== LOGGING SETUP ====================
# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'api.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger("rainfall_api")

# ==================== REQUEST MODELS ====================
class AdvisoryRequest(BaseModel):
    user_id: str
    gps_lat: float
    gps_long: float
    date: str  # Format: YYYY-MM-DD
    
    @field_validator('gps_lat')
    @classmethod
    def validate_latitude(cls, v):
        if not (12.5 <= v <= 14.5):
            raise ValueError('GPS latitude out of Udupi district range (12.5-14.5)')
        return v
    
    @field_validator('gps_long')
    @classmethod
    def validate_longitude(cls, v):
        if not (74.4 <= v <= 75.3):
            raise ValueError('GPS longitude out of Udupi district range (74.4-75.3)')
        return v
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        try:
            dt = datetime.strptime(v, '%Y-%m-%d')
            today = datetime.now()
            diff = (dt - today).days
            if diff > 30:
                raise ValueError('Date cannot be more than 30 days in future')
            if diff < -3650:  # Extended to 10 years for historical validation
                raise ValueError('Date cannot be more than 10 years in past')
            return v
        except ValueError as e:
            raise ValueError(f'Invalid date format. Use YYYY-MM-DD. Error: {str(e)}')

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str

# ==================== FASTAPI APP ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Rainfall Advisory API Starting")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Debug Mode: {os.getenv('DEBUG', 'False')}")
    
    # Initialize Singletons (Performance Optimization)
    try:
        logger.info("Initializing ML Models and Data Engines...")
        app.state.mapper = TalukMapper()
        app.state.engineer = FeatureEngineer()
        app.state.predictor = RainfallPredictor()
        logger.info("✅ Initialization Complete")
    except Exception as e:
        logger.error(f"❌ Initialization Failed: {e}")
        # We don't raise here to allow health check to report failure if needed, 
        # or we could crash hard. For now, let's log critical error.
    
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("🛑 Rainfall Advisory API Shutting Down")
    # Clear resources if needed
    app.state.mapper = None
    app.state.engineer = None
    app.state.predictor = None

# Prediction logging (separate file for audit)
prediction_logger = logging.getLogger("predictions")
prediction_handler = logging.FileHandler(LOG_DIR / 'predictions.log')
prediction_handler.setFormatter(logging.Formatter('%(message)s'))
prediction_logger.addHandler(prediction_handler)
prediction_logger.setLevel(logging.INFO)

# ==================== ENVIRONMENT CONFIG ====================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ==================== RATE LIMITING ====================
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Rainfall Advisory API",
    version="1.2",
    description="ML-powered rainfall prediction and farmer advisory system",
    debug=DEBUG,
    lifespan=lifespan
)

# Add Gzip compression for faster responses
app.add_middleware(GZipMiddleware, minimum_size=500)  # Compress responses > 500 bytes

# ... (middleware/handlers remain same) ...

# ==================== ENDPOINTS ====================
@app.get("/", response_model=dict)
def root():
    """API information"""
    return {
        "service": "Rainfall Advisory API",
        "version": "1.2",
        "status": "online",
        "environment": ENVIRONMENT,
        "endpoints": {
            "advisory": "/get-advisory",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint for Render and monitoring
    Returns 200 if all dependencies are accessible
    """
    try:
        # Check if critical files exist (using BASE_DIR for resolution)
        required_files = [
            settings.RAINFALL_DATA_PATH,
            settings.WEATHER_DATA_PATH,
            settings.DISTRICT_MODEL_PATH,
            settings.FEATURE_SCHEMA_PATH,
            settings.BASE_DIR / "data/taluk_boundaries.json"
        ]
        
        missing_files = [str(f) for f in required_files if not f.exists()]
        
        if missing_files:
            logger.error(f"Health check failed: Missing files {missing_files}")
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: Missing data files {missing_files}"
            )
        
        return HealthResponse(
            status="healthy",
            version="1.2",
            environment=ENVIRONMENT,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/metrics")
def get_metrics():
    """
    Enhanced metrics endpoint with drift and performance tracking
    """
    try:
        # Count predictions from log file
        prediction_log = LOG_DIR / 'predictions.log'
        if prediction_log.exists():
            with open(prediction_log, 'r') as f:
                total_predictions = sum(1 for _ in f)
        else:
            total_predictions = 0
        
        # Get drift summary
        from .monitoring.drift import get_drift_detector
        drift_detector = get_drift_detector()
        drift_summary = drift_detector.get_drift_summary(last_n_hours=24)
        
        # Get performance metrics
        from .monitoring.quality import get_performance_tracker
        tracker = get_performance_tracker()
        perf_metrics = tracker.get_latest_metrics()
        
        return {
            "total_predictions": total_predictions,
            "status": "operational",
            "version": "1.2",
            "drift_alerts_24h": drift_summary,
            "performance": perf_metrics
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"error": "Could not fetch metrics"}

@app.get("/monitoring/drift")
def get_drift_status():
    """
    Dedicated drift monitoring endpoint
    """
    from .monitoring.drift import get_drift_detector
    drift_detector = get_drift_detector()
    return drift_detector.get_drift_summary(last_n_hours=168)  # 7 days

@app.get("/monitoring/performance")
def get_performance_stats():
    """
    Dedicated performance metrics endpoint
    """
    from .monitoring.quality import get_performance_tracker
    tracker = get_performance_tracker()
    return {
        "metrics": tracker.get_latest_metrics(),
        "by_taluk": tracker.get_prediction_stats_by_taluk()
    }

@app.post("/get-advisory")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def get_advisory(request: Request, advisory_request: AdvisoryRequest):
    """
    Main endpoint: Returns rainfall prediction and farmer advisory.
    Rate limited to 10 requests/minute per IP.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing advisory for user: {advisory_request.user_id}")
        
        # Dependency Injection for Performance
        result = process_advisory_request(
            advisory_request.user_id,
            advisory_request.gps_lat,
            advisory_request.gps_long,
            advisory_request.date,
            mapper=getattr(request.app.state, 'mapper', None),
            engineer=getattr(request.app.state, 'engineer', None),
            predictor=getattr(request.app.state, 'predictor', None)
        )
        
        if result['status'] == 'error':
            logger.error(f"Advisory processing error: {result.get('message')}")
            # Identify if it's a client error (400) or server error (500)
            error_type = result.get('error', {}).get('type', 'system_error')
            status_code = 400 if error_type in ['gps_error', 'date_error'] else 500
            
            # For 500 errors, we might want to return a cleaner message
            detail = result.get('message', 'Processing error')
            if status_code == 500 and result.get('error', {}).get('technical_message'):
                 # Log technical detail but send user friendly one
                 logger.error(f"Technical error: {result['error']['technical_message']}")
            
            # Actually, process_advisory_request returns a farmer-friendly error dict
            # We should probably return IT as JSON with 400/500 status, not raise HTTPException
            # because the frontend expects this JSON structure.
            return JSONResponse(status_code=status_code, content=result)

        
        # ... (rest of logging logic same) ...
        # DRIFT DETECTION: Check if inputs are unusual
        from .monitoring.drift import get_drift_detector
        drift_detector = get_drift_detector()
        
        # PERFORMANCE TRACKING: Log prediction
        from .monitoring.quality import get_performance_tracker
        tracker = get_performance_tracker()
        
        # Handle both old and new response formats
        taluk_name = result.get('location', {}).get('taluk', result.get('location', {}).get('area', 'Unknown'))
        main_prediction = result.get('prediction', {}).get('month_status') or result.get('rainfall', {}).get('monthly_prediction', {}).get('category', 'Unknown')
        
        # FIX: Get full confidence dict from technical_details if available, else fallback
        confidence = result.get('technical_details', {}).get('confidence_scores') or result.get('prediction', {}).get('confidence', {})
        
        # Logic to determine if alert was shown
        alert_shown = False
        if 'alert' in result:
             alert_shown = result['alert'].get('show_alert', False)
        elif 'main_status' in result:
             alert_shown = result['main_status'].get('priority') in ['WARNING', 'URGENT', 'CRITICAL']

        tracker.log_prediction(
            user_id=advisory_request.user_id,
            taluk=taluk_name,
            features={},  # Would include actual features in production
            prediction=main_prediction,
            confidence=confidence,
            alert_sent=alert_shown
        )
        
        # Log prediction for audit
        prediction_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": advisory_request.user_id,
            "gps": f"{advisory_request.gps_lat},{advisory_request.gps_long}",
            "taluk": taluk_name,
            "prediction": main_prediction,
            "alert_sent": alert_shown,
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        }
        prediction_logger.info(json.dumps(prediction_log_entry))
        
        logger.info(f"Advisory complete for {advisory_request.user_id}: {main_prediction}")
        
        return result
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/get-enhanced-advisory", response_model=dict)
@limiter.limit("60/minute")
async def get_enhanced_advisory(request: Request, advisory_req: AdvisoryRequest):
    """
    Enhanced Farmer Advisory with 7-day weather forecast and crop advice.
    """
    try:
        # Get basic prediction
        result = process_advisory_request(
            advisory_req.user_id,
            advisory_req.gps_lat,
            advisory_req.gps_long,
            advisory_req.date,
            mapper=getattr(request.app.state, 'mapper', None),
            engineer=getattr(request.app.state, 'engineer', None),
            predictor=getattr(request.app.state, 'predictor', None)
        )
        
        if result['status'] != 'success':
            # Return error as regular response or raise HTTP exception depending on client needs
            # Here we raise for consistency with previous implementation
             raise HTTPException(status_code=400, detail=result.get('error', {}).get('message', 'Prediction failed'))
        
        # Generate enhanced advisory
        advisor = AdvisoryService()
        
        # New: Extract history for improved soil moisture est
        history = result.get('technical_details', {}).get('rainfall_history')
        
        enhanced = advisor.generate_complete_advisory(
            result,
            lat=advisory_req.gps_lat,
            lon=advisory_req.gps_long,
            crops=['paddy', 'coconut', 'vegetables'],  # Default Udupi crops
            rainfall_history=history
        )
        
        # Combine with original prediction
        enhanced_result = {
            **result,
            'enhanced_advisory': enhanced,
            'api_version': '1.2'
        }
        
        return enhanced_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced advisory error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate advisory: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
