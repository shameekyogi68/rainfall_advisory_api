from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import json
import os
from pathlib import Path

from production_backend import process_advisory_request
from farmer_advisory import FarmerAdvisory

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

logger.info(f"Starting API in {ENVIRONMENT} mode")

# ==================== RATE LIMITING ====================
limiter = Limiter(key_func=get_remote_address)

# ==================== REQUEST MODELS ====================
class AdvisoryRequest(BaseModel):
    user_id: str
    gps_lat: float
    gps_long: float
    date: str  # Format: YYYY-MM-DD
    
    @validator('gps_lat')
    def validate_latitude(cls, v):
        if not (12.5 <= v <= 14.5):
            raise ValueError('GPS latitude out of Udupi district range (12.5-14.5)')
        return v
    
    @validator('gps_long')
    def validate_longitude(cls, v):
        if not (74.4 <= v <= 75.3):
            raise ValueError('GPS longitude out of Udupi district range (74.4-75.3)')
        return v
    
    @validator('date')
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
app = FastAPI(
    title="Rainfall Advisory API",
    version="1.1",
    description="ML-powered rainfall prediction and farmer advisory system",
    debug=DEBUG
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==================== CORS CONFIGURATION ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ==================== ERROR HANDLERS ====================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error. Please try again later.",
            "error_code": "INTERNAL_ERROR"
        }
    )

# ==================== MIDDLEWARE ====================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.now()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
    
    try:
        response = await call_next(request)
        
        # Log response
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Response: {response.status_code} in {duration:.3f}s")
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}", exc_info=True)
        raise

# ==================== ENDPOINTS ====================
@app.get("/", response_model=dict)
def root():
    """API information"""
    return {
        "service": "Rainfall Advisory API",
        "version": "1.1",
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
        # Check if critical files exist
        required_files = [
            "rainfall_daily_historical_v1.csv",
            "weather_drivers_daily_v1.csv",
            "final_rainfall_classifier_v1.pkl",
            "feature_schema_v1.json",
            "taluk_boundaries.json"
        ]
        
        missing_files = [f for f in required_files if not Path(f).exists()]
        
        if missing_files:
            logger.error(f"Health check failed: Missing files {missing_files}")
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: Missing data files {missing_files}"
            )
        
        return HealthResponse(
            status="healthy",
            version="1.1",
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
        from drift_monitor import get_drift_detector
        drift_detector = get_drift_detector()
        drift_summary = drift_detector.get_drift_summary(last_n_hours=24)
        
        # Get performance metrics
        from performance_tracker import get_performance_tracker
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
    from drift_monitor import get_drift_detector
    drift_detector = get_drift_detector()
    return drift_detector.get_drift_summary(last_n_hours=168)  # 7 days

@app.get("/monitoring/performance")
def get_performance_stats():
    """
    Dedicated performance metrics endpoint
    """
    from performance_tracker import get_performance_tracker
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
        
        result = process_advisory_request(
            advisory_request.user_id,
            advisory_request.gps_lat,
            advisory_request.gps_long,
            advisory_request.date
        )
        
        if result['status'] == 'error':
            logger.error(f"Advisory processing error: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get('message', 'Processing error'))
        
        # DRIFT DETECTION: Check if inputs are unusual
        from drift_monitor import get_drift_detector
        drift_detector = get_drift_detector()
        
        # Get features from result (they were computed in production_backend)
        # For now, we'll extract from the internal processing
        # In a real setup, production_backend would return features
        
        # PERFORMANCE TRACKING: Log prediction
        from performance_tracker import get_performance_tracker
        tracker = get_performance_tracker()
        
        # Handle both old and new response formats
        taluk_name = result['location'].get('taluk', result['location'].get('area', 'Unknown'))
        main_prediction = result.get('prediction', {}).get('month_status') or result.get('rainfall', {}).get('monthly_prediction', {}).get('category', 'Unknown')
        confidence = result.get('prediction', {}).get('confidence', {})
        alert_shown = result.get('alert', {}).get('show_alert', False) or result.get('main_status', {}).get('priority') in ['WARNING', 'URGENT']
        
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
            "alert_level": result.get('alert', {}).get('level', result.get('main_status', {}).get('priority', 'UNKNOWN')),
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

# ==================== STARTUP EVENT ====================
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("🚀 Rainfall Advisory API Starting")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Debug Mode: {DEBUG}")
    logger.info(f"Allowed Origins: {ALLOWED_ORIGINS}")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown"""
    logger.info("🛑 Rainfall Advisory API Shutting Down")

# ==================== RUN SERVER ====================


@app.post("/get-enhanced-advisory", response_model=dict)
@limiter.limit("60/minute")
async def get_enhanced_advisory(request: Request, advisory_req: AdvisoryRequest):
    """
    Enhanced Farmer Advisory with:
    - 7-day weather forecast
    - Actionable recommendations  
    - Crop-specific advice
    - Risk levels
    """
    try:
        # Get basic prediction
        result = process_advisory_request(
            request_id=f"enhanced_{datetime.now().timestamp()}",
            lat=advisory_req.latitude,
            lon=advisory_req.longitude,
            date_str=advisory_req.date
        )
        
        if result['status'] != 'success':
            raise HTTPException(status_code=400, detail=result.get('error', 'Prediction failed'))
        
        # Generate enhanced advisory
        advisor = FarmerAdvisory()
        enhanced = advisor.generate_complete_advisory(
            result,
            lat=advisory_req.latitude,
            lon=advisory_req.longitude,
            crops=['paddy', 'coconut', 'vegetables']  # Default Udupi crops
        )
        
        # Combine with original prediction
        enhanced_result = {
            **result,
            'enhanced_advisory': enhanced,
            'api_version': '1.2'
        }
        
        # Log enhanced request
        prediction_logger.info(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "type": "enhanced_advisory",
            "location": {"lat": advisory_req.latitude, "lon": advisory_req.longitude},
            "prediction": result['rainfall']['monthly_prediction']['category'],
            "confidence": result['rainfall']['monthly_prediction']['confidence_percent']
        }))
        
        return enhanced_result
        
    except  HTTPException:
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
