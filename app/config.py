# Configuration Management
# Environment variables for production settings

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Application configuration from environment variables"""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Rainfall Advisory API"
    API_VERSION: str = "2.0.0"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100
    
    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Model Paths
    DISTRICT_MODEL_PATH: Path = BASE_DIR / "models/final_rainfall_classifier_v1.pkl"
    TALUK_MODELS_PATH: Path = BASE_DIR / "models/taluk_models.pkl"
    FEATURE_SCHEMA_PATH: Path = BASE_DIR / "data/feature_schema_v1.json"
    
    # Data Paths
    RAINFALL_DATA_PATH: Path = BASE_DIR / "data/rainfall_daily_historical_v1.csv"
    WEATHER_DATA_PATH: Path = BASE_DIR / "data/weather_drivers_daily_v1.csv"
    MONTHLY_TARGETS_PATH: Path = BASE_DIR / "data/rainfall_monthly_targets_v2_CORRECTED.csv"
    
    # External APIs
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_API_TIMEOUT: int = 10
    
    # Model Parameters
    ROLLING_WINDOW_DAYS: int = 30
    HISTORICAL_WINDOW_DAYS: int = 90
    FEATURES_COUNT: int = 12
    
    # Security
    API_KEY_ENABLED: bool = False
    API_KEYS: str = ""  # Comma-separated list
    CORS_ORIGINS: str = "*"  # Comma-separated list
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "rainfall_api.log"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True
    
    # Cache
    ENABLE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def api_keys_list(self) -> list:
        """Parse API keys from comma-separated string"""
        if not self.API_KEYS:
            return []
        return [key.strip() for key in self.API_KEYS.split(',')]
    
    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins from comma-separated string"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

# Global settings instance
settings = Settings()
