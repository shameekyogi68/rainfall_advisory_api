#!/usr/bin/env python3
"""
Comprehensive Validation Script for Rainfall Advisory API
Tests present and future dates, validates prediction accuracy
"""

from production_backend import process_advisory_request
import json
from datetime import datetime, timedelta

def validate_prediction(result, date_str):
    """Validate if prediction is reasonable"""
    print(f"\n{'='*60}")
    print(f"📅 Testing Date: {date_str}")
    print(f"{'='*60}")
    
    if result['status'] != 'success':
        print(f"❌ FAILED: {result['error']['message']['en']}")
        return False
    
    # Extract key info
    location = result['location']['area']
    prediction = result['rainfall']['monthly_prediction']['category']
    confidence = result['rainfall']['monthly_prediction']['confidence_percent']
    forecast_7d = result['rainfall']['next_7_days']['amount_mm']
    action = result['what_to_do']['actions'][0]['en']
    priority = result['main_status']['priority']
    
    print(f"📍 Location: {location}")
    print(f"🌧️ Monthly Prediction: {prediction} ({confidence}% confidence)")
    print(f"☔ 7-Day Forecast: {forecast_7d}mm")
    print(f"⚠️  Alert Priority: {priority}")
    print(f"💡 Recommended Action: {action}")
    
    # Validation checks
    issues = []
    
    # 1. Check if confidence is realistic (not too extreme)
    if confidence < 30:
        issues.append(f"⚠️  Low confidence ({confidence}%) - model uncertain")
    elif confidence > 95:
        issues.append(f"⚠️  Unusually high confidence ({confidence}%) - possible overfitting")
    
    # 2. Check if forecast and prediction align
    if prediction == "Deficit" and forecast_7d > 50:
        issues.append(f"❌ MISMATCH: Deficit prediction but heavy rain forecast ({forecast_7d}mm)")
    elif prediction == "Excess" and forecast_7d < 10:
        issues.append(f"❌ MISMATCH: Excess prediction but low rain forecast ({forecast_7d}mm)")
    
    # 3. Check if actions match the scenario
    if prediction == "Deficit" and "water" not in action.lower():
        issues.append(f"❌ MISMATCH: Deficit prediction but no irrigation action")
    
    # 4. Validate data sources
    data_source = result['data_sources']['weather_forecast']
    print(f"📡 Weather Data: {data_source}")
    
    if data_source == "historical_estimate":
        print(f"ℹ️  Using historical estimate (weather API unavailable)")
    
    # Print validation results
    print(f"\n{'─'*60}")
    if issues:
        print("⚠️  VALIDATION ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print(f"{'─'*60}")
        return False
    else:
        print("✅ VALIDATION PASSED - Prediction appears reasonable")
        print(f"{'─'*60}")
        return True

# Test dates
test_cases = [
    ("2026-02-06", "TODAY - Current date"),
    ("2026-02-07", "TOMORROW - Next day"),
    ("2026-02-10", "4 days ahead"),
    ("2026-02-15", "Next week"),
    ("2026-03-01", "Future month (March)"),
]

print("""
╔═════════════════════════════════════════════════════════════╗
║       RAINFALL ADVISORY API - VALIDATION TESTS              ║
║       Testing Present & Future Date Predictions             ║
╚═════════════════════════════════════════════════════════════╝
""")

# Test coordinates (Udupi city center)
test_lat = 13.3409
test_lon = 74.7421

results_summary = []

for date_str, description in test_cases:
    try:
        result = process_advisory_request(
            user_id='validation_test',
            gps_lat=test_lat,
            gps_long=test_lon,
            date_str=date_str
        )
        
        is_valid = validate_prediction(result, f"{date_str} ({description})")
        results_summary.append((date_str, description, is_valid))
        
    except Exception as e:
        print(f"\n❌ ERROR for {date_str}: {str(e)}")
        results_summary.append((date_str, description, False))

# Final summary
print(f"\n\n{'═'*60}")
print("📊 VALIDATION SUMMARY")
print(f"{'═'*60}")

passed = sum(1 for _, _, valid in results_summary if valid)
total = len(results_summary)

for date, desc, valid in results_summary:
    status = "✅ PASS" if valid else "❌ FAIL"
    print(f"{status} | {date} ({desc})")

print(f"{'─'*60}")
print(f"Results: {passed}/{total} tests passed ({int(passed/total*100)}%)")
print(f"{'═'*60}\n")

if passed == total:
    print("🎉 ALL TESTS PASSED - API is working correctly!")
else:
    print("⚠️  Some tests failed - Review issues above")
