# Rainfall Advisory API - Production System

ML-powered rainfall prediction and farmer advisory system for Udupi District, Karnataka.

**Live API:** [https://rainfall-advisory-api-1.onrender.com](https://rainfall-advisory-api-1.onrender.com)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 🚀 Quick Start

### Deploy to Render (Recommended)

**Option 1: One-Click Deploy**
1. Click the "Deploy to Render" button above
2. Connect your GitHub repository
3. Render will automatically use `render.yaml` for configuration
4. Click "Deploy"

**Option 2: Manual Deploy**
1. **Fork/Clone this repository**
2. **Connect to Render**:
   - Go to [render.com](https://render.com)
   - New Web Service → Connect repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
3. **Set Environment Variables**:
   ```
   ENVIRONMENT=production
   DEBUG=False
   ALLOWED_ORIGINS=*
   ```
4. **Deploy!**

---

## 📡 API Endpoints

### Main Endpoint
**POST** `/get-advisory`

**Request**:
```json
{
  "user_id": "farmer_123",
  "gps_lat": 13.3409,
  "gps_long": 74.7421,
  "date": "2025-06-15"
}
```

**Response**:
```json
{
  "status": "success",
  "location": {
    "taluk": "Udupi",
    "district": "Udupi",
    "confidence": "high"
  },
  "prediction": {
    "month_status": "Normal",
    "confidence": {
      "Deficit": 0.05,
      "Normal": 0.77,
      "Excess": 0.18
    }
  },
  "alert": {
    "show_alert": false,
    "level": "LOW",
    "title": "Normal conditions...",
    "message": "..."
  }
}
```

### Monitoring Endpoints

- **GET** `/health` - Health check
- **GET** `/metrics` - System metrics with drift and performance
- **GET** `/monitoring/drift` - Drift detection summary
- **GET** `/monitoring/performance` - Performance breakdown

---

## 🧪 Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run automated tests
pytest test_backend.py -v

# Run deployment verification (all-in-one test)
./verify_deployment.sh

# Test API locally
python3 api_server.py
# Then visit: http://localhost:8000/docs
```

### Deployment Verification Script

The `verify_deployment.sh` script performs comprehensive testing:
- ✅ All API endpoints (health, metrics, advisory)
- ✅ Data file integrity
- ✅ Configuration files
- ✅ Error handling
- ✅ Request validation

Run before deploying to ensure production readiness!

---

## 📊 System Components

| Component | File | Purpose |
|-----------|------|---------|
| API Server | `api_server.py` | FastAPI REST endpoint |
| ML Pipeline | `production_backend.py` | GPS mapping, features, inference |
| Decision Logic | `decision_rules.py` | Alert generation |
| Drift Monitor | `drift_monitor.py` | Data drift detection |
| Performance Tracker | `performance_tracker.py` | Metrics logging |

---

## 📦 Data Files

| File | Size | Purpose |
|------|------|---------|
| `final_rainfall_classifier_v1.pkl` | 14MB | Trained Random Forest model |
| `training_table_v2_CORRECTED.csv` | 1.1MB | ML training data |
| `rainfall_daily_historical_v1.csv` | 362KB | Historical rainfall |
| `weather_drivers_daily_v1.csv` | 642KB | Weather features |
| `rainfall_monthly_targets_v2_CORRECTED.csv` | 14KB | Target categories |
| `taluk_boundaries.json` | 2KB | GPS boundaries |
| `feature_schema_v1.json` | 338B | Feature schema |

**Total**: ~17MB

---

## 🔒 Security

- ✅ Rate limiting: 10 requests/minute per IP
- ✅ Input validation (GPS bounds, date format)
- ✅ CORS protection (configurable)
- ✅ Environment-based configuration
- ✅ Error handling (no stack traces exposed)

---

## 📈 Monitoring

View system health:
```bash
curl https://rainfall-advisory-api-1.onrender.com/metrics
```

Returns:
- Total predictions
- Drift alerts (24h)
- Performance metrics
- Category distribution

---

## 🔄 CI/CD

GitHub Actions automatically:
- ✅ Runs tests on every push
- ✅ Checks code quality
- ✅ Deploys to Render on main branch

---

## 🛠️ Local Development

```bash
# Clone repository
git clone YOUR_REPO_URL
cd data_converter

# Install dependencies
pip3 install -r requirements.txt

# Run locally
python3 api_server.py

# Visit API docs
open http://localhost:8000/docs
```

---

## 📱 Flutter Integration

```dart
final response = await http.post(
  Uri.parse('$apiUrl/get-advisory'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_id': userId,
    'gps_lat': position.latitude,
    'gps_long': position.longitude,
    'date': DateFormat('yyyy-MM-dd').format(DateTime.now()),
  }),
);

if (response.statusCode == 200) {
  final advisory = jsonDecode(response.body);
  // Use advisory data
}
```

---

- [Complete MLOps Guide](docs/mlops_complete.md)
- [Render Deployment Guide](docs/render_deployment.md)
- [API Contract](docs/backend_api_contract.md)
- [Detailed API Documentation (English/Kannada)](file:///Users/shameekyogi/.gemini/antigravity/brain/d0a27a69-f7c4-470d-a360-7523c6f15cd6/api_documentation.md)

---

## 🎯 Model Info

- **Type**: Random Forest Classifier
- **Version**: v1 (Frozen)
- **Categories**: Deficit, Normal, Excess
- **Features**: 8 (lag features + weather + month)
- **Training Period**: 2020-2023
- **Accuracy**: 74%
- **Deficit Recall**: 77% (safety-focused)

---

## 📊 MLOps Maturity

**Level**: 3/5 (Production-Ready)
**Compliance**: 87%

Implemented:
- ✅ Data versioning
- ✅ Model versioning
- ✅ Feature schema
- ✅ Drift detection
- ✅ Performance tracking
- ✅ Automated testing
- ✅ CI/CD pipeline
- ✅ Monitoring endpoints

---

## 🙏 Credits

Built for farmers in Udupi District, Karnataka
ML Model: Random Forest (scikit-learn)
Weather API: Open-Meteo (free tier)

---

## 📝 License

Proprietary - For farmer advisory use only

---

**Version**: 1.2  
**Last Updated**: 2026-02-27  
**Status**: Production-Ready ✅
