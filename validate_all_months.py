#!/usr/bin/env python3
"""
Comprehensive Year-Round Validation Script
Tests all 12 months with real weather API data
"""

from production_backend import process_advisory_request, get_live_forecast_safe
import json
from datetime import datetime, timedelta
import pandas as pd

# Udupi seasonal rainfall patterns (mm/month average)
UDUPI_SEASONAL_PATTERNS = {
    1: {"name": "January", "expected_rain": "Very Low (2-5mm)", "season": "Dry", "ml_should_predict": "Deficit"},
    2: {"name": "February", "expected_rain": "Very Low (2-5mm)", "season": "Dry", "ml_should_predict": "Deficit"},
    3: {"name": "March", "expected_rain": "Low (5-20mm)", "season": "Pre-Monsoon", "ml_should_predict": "Deficit/Normal"},
    4: {"name": "April", "expected_rain": "Moderate (50-80mm)", "season": "Pre-Monsoon", "ml_should_predict": "Normal"},
    5: {"name": "May", "expected_rain": "High (100-150mm)", "season": "Pre-Monsoon", "ml_should_predict": "Normal/Excess"},
    6: {"name": "June", "expected_rain": "Very High (500-800mm)", "season": "SW Monsoon", "ml_should_predict": "Excess"},
    7: {"name": "July", "expected_rain": "Very High (600-900mm)", "season": "SW Monsoon", "ml_should_predict": "Excess"},
    8: {"name": "August", "expected_rain": "Very High (500-700mm)", "season": "SW Monsoon", "ml_should_predict": "Excess"},
    9: {"name": "September", "expected_rain": "High (250-400mm)", "season": "SW Monsoon", "ml_should_predict": "Excess"},
    10: {"name": "October", "expected_rain": "Moderate (150-250mm)", "season": "NE Monsoon", "ml_should_predict": "Normal/Excess"},
    11: {"name": "November", "expected_rain": "Low (50-100mm)", "season": "NE Monsoon", "ml_should_predict": "Normal"},
    12: {"name": "December", "expected_rain": "Very Low (10-30mm)", "season": "Dry", "ml_should_predict": "Deficit/Normal"}
}

def validate_month(month, year=2026):
    """Validate a specific month"""
    # Test 1st and 15th of each month
    dates_to_test = [
        f"{year}-{month:02d}-01",
        f"{year}-{month:02d}-15"
    ]
    
    month_info = UDUPI_SEASONAL_PATTERNS.get(month, {})
    results = []
    
    print(f"\n{'='*70}")
    print(f"📅 MONTH {month}: {month_info.get('name', 'Unknown').upper()}")
    print(f"   Season: {month_info.get('season')}")
    print(f"   Expected: {month_info.get('expected_rain')}")
    print(f"   ML Should Predict: {month_info.get('ml_should_predict')}")
    print(f"{'='*70}")
    
    for date_str in dates_to_test:
        try:
            # Get ML prediction
            result = process_advisory_request(
                user_id='validation',
                gps_lat=13.3409,
                gps_long=74.7421,
                date_str=date_str
            )
            
            if result['status'] != 'success':
                print(f"❌ {date_str}: API Error")
                results.append({'date': date_str, 'valid': False, 'reason': 'API Error'})
                continue
            
            ml_prediction = result['rainfall']['monthly_prediction']['category']
            confidence = result['rainfall']['monthly_prediction']['confidence_percent']
            forecast_7d = result['rainfall']['next_7_days']['amount_mm']
            weather_source = result['data_sources']['weather_forecast']
            priority = result['main_status']['priority']
            
            # Validate
            issues = []
            
            # Check if ML prediction aligns with season
            expected_predictions = month_info.get('ml_should_predict', '').split('/')
            if ml_prediction not in expected_predictions:
                issues.append(f"ML predicts '{ml_prediction}' but season expects '{month_info.get('ml_should_predict')}'")
            
            # Check monsoon months (June-Sep)
            if month in [6, 7, 8, 9]:
                if ml_prediction != "Excess":
                    issues.append(f"Monsoon month but ML predicts '{ml_prediction}' instead of 'Excess'")
            
            # Check dry season (Dec-Feb)
            if month in [12, 1, 2]:
                if ml_prediction == "Excess":
                    issues.append(f"Dry season but ML predicts 'Excess' (should be Deficit/Normal)")
            
            # Print result
            status = "✅" if not issues else "⚠️"
            print(f"\n{status} {date_str}:")
            print(f"   ML Prediction: {ml_prediction} ({confidence}%)")
            print(f"   7-Day Forecast: {forecast_7d}mm ({weather_source})")
            print(f"   Priority: {priority}")
            
            if issues:
                print(f"   ⚠️ ISSUES:")
                for issue in issues:
                    print(f"      - {issue}")
                results.append({'date': date_str, 'valid': False, 'issues': issues})
            else:
                print(f"   ✅ Validated")
                results.append({'date': date_str, 'valid': True})
                
        except Exception as e:
            print(f"❌ {date_str}: Error - {str(e)}")
            results.append({'date': date_str, 'valid': False, 'reason': str(e)})
    
    return results

# Main validation
print("""
╔══════════════════════════════════════════════════════════════════╗
║        COMPREHENSIVE YEAR-ROUND VALIDATION                       ║
║        Testing All 12 Months with Real Weather Data             ║
╚══════════════════════════════════════════════════════════════════╝
""")

all_results = {}

for month in range(1, 13):
    month_results = validate_month(month)
    all_results[month] = month_results

# Summary
print(f"\n\n{'='*70}")
print("📊 VALIDATION SUMMARY")
print(f"{'='*70}")

total_tests = 0
passed_tests = 0
failed_by_month = {}

for month, results in all_results.items():
    month_name = UDUPI_SEASONAL_PATTERNS[month]['name']
    valid_count = sum(1 for r in results if r.get('valid', False))
    total_count = len(results)
    
    total_tests += total_count
    passed_tests += valid_count
    
    status = "✅" if valid_count == total_count else "⚠️"
    print(f"{status} {month_name:12} : {valid_count}/{total_count} tests passed")
    
    if valid_count < total_count:
        failed_by_month[month_name] = [r for r in results if not r.get('valid', False)]

print(f"\n{'─'*70}")
print(f"OVERALL: {passed_tests}/{total_tests} tests passed ({int(passed_tests/total_tests*100)}%)")
print(f"{'='*70}\n")

if failed_by_month:
    print("⚠️ DETAILED ISSUES BY MONTH:\n")
    for month_name, failed in failed_by_month.items():
        print(f"{month_name}:")
        for result in failed:
            print(f"  {result['date']}: {result.get('issues', result.get('reason', 'Unknown'))}")
        print()

if passed_tests == total_tests:
    print("🎉 ALL TESTS PASSED - System validated across all seasons!")
else:
    print(f"⚠️ {total_tests - passed_tests} tests failed - Review issues above")
