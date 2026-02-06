# Large Data Files - Not Included in Repository

The following directories contain large data files (>7GB total) that are **excluded from Git** due to size constraints:

## Excluded Directories

- **`DCS/`** (~21 MB) - NetCDF daily climate summary files
- **`chirps/`** (~7 GB) - CHIRPS rainfall data NetCDF files
- **`Nasa Power/`** (~504 KB) - NASA POWER weather CSV files
- **`taluk_csv/`** (~360 KB) - Taluk-wise rainfall CSV files
- **`taluk_daily_csv/`** (~324 KB) - Daily taluk rainfall data

## Why Excluded?

1. **Size**: Total ~7GB would exceed GitHub's limits
2. **Disk Space**: System disk is at 99% capacity
3. **Not Required for API**: The processed CSV and model files are sufficient for the API to function

## Files Included in Repository

✅ **All essential files are included:**
- `final_rainfall_classifier_v1.pkl` (14 MB) - Trained ML model
- `rainfall_daily_historical_v1.csv` (354 KB) - Historical data
- `weather_drivers_daily_v1.csv` (627 KB) - Weather features
- `training_table_v1.csv` (1.1 MB) - Training dataset
- `rainfall_monthly_targets_v1.csv` (14 KB) - Target categories
- `taluk_boundaries.json` (1.9 KB) - GPS boundaries
- `feature_schema_v1.json` (338 B) - Feature definitions

## API Functionality

The API **works perfectly** without the excluded directories. All required data for:
- GPS to taluk mapping
- Feature engineering
- ML predictions
- Weather API integration

...is contained in the included CSV and JSON files.

## Deployment to Render

✅ **No issues** - Render deployment works without these directories.

The excluded files were only used during:
- Initial data collection and processing
- Model training
- Data validation

They are **not needed** for the production API runtime.
