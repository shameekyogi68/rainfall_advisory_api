#!/usr/bin/env python3
"""
Test NEW Model on Real Monsoon Dates
Compare with old model performance
"""

import pandas as pd
import pickle
import numpy as np

# Load both models
print('='*70)
print('VALIDATING NEW MODEL ON REAL MONSOON DATES')
print('='*70)

print('\n1. Loading models...')
with open('final_rainfall_classifier_v1.pkl', 'rb') as f:
    old_model = pickle.load(f)
    
with open('final_rainfall_classifier_v2_CORRECTED.pkl', 'rb') as f:
    new_model = pickle.load(f)

print('   ✅ Old model (v1) loaded')
print('   ✅ New model (v2 CORRECTED) loaded')

# Load test data
df = pd.read_csv('training_table_v2_CORRECTED.csv')

# Test cases - real dates with known heavy rainfall
test_cases = [
    ('2025-07-15', 'July 2025 Peak Monsoon (1,590mm)'),
    ('2025-06-20', 'June 2025 Monsoon Start (1,063mm)'),
    ('2025-08-15', 'August 2025 Monsoon (1,276mm)'),
    ('2026-02-01', 'February 2026 Dry Season (3-5mm)'),
    ('2025-01-15', 'January 2025 Dry (1mm)'),
]

print('\n' + '='*70)
print('TEST RESULTS')
print('='*70)

results = []

for date_str, description in test_cases:
    # Find closest date in training data
    test_sample = df[df['date'] == date_str]
    
    if len(test_sample) == 0:
        # Try to find any sample from that month/year
        year = int(date_str[:4])
        month = int(date_str[5:7])
        test_sample = df[(df['date'].str.startswith(f'{year}-{month:02d}'))]
        
        if len(test_sample) == 0:
            print(f'\n❌ No data for {date_str}')
            continue
        
        test_sample = test_sample.head(1)
    
    # Get features
    feature_cols = ['rain_lag_7', 'rain_lag_30', 'rolling_30_rain',
                    'temp', 'humidity', 'wind', 'pressure', 'month']
    
    X = test_sample[feature_cols].values
    actual_label = test_sample.iloc[0]['target_category']
    monthly_rain = test_sample.iloc[0]['target_monthly_rain']
    month = test_sample.iloc[0]['month']
    
    # Predict with both models
    old_pred = old_model.predict(X)[0]
    old_proba = old_model.predict_proba(X)[0]
    old_confidence = max(old_proba) * 100
    
    new_pred = new_model.predict(X)[0]
    new_proba = new_model.predict_proba(X)[0]
    new_confidence = max(new_proba) * 100
    
    # Expected
    if month in [6, 7, 8]:
        expected = 'Excess' if monthly_rain > 1200 else 'Normal'
    elif month in [1, 2]:
        expected = 'Deficit'
    else:
        expected = actual_label
    
    # Evaluate
    old_correct = (old_pred == expected)
    new_correct = (new_pred == expected)
    
    print(f'\n📅 {date_str} - {description}')
    print(f'   Monthly Rainfall: {monthly_rain:.0f}mm')
    print(f'   Expected: {expected}')
    print(f'   Old Model v1: {old_pred} ({old_confidence:.0f}%) {"✅" if old_correct else "❌"}')
    print(f'   New Model v2: {new_pred} ({new_confidence:.0f}%) {"✅" if new_correct else "❌"}')
    
    results.append({
        'date': date_str,
        'description': description,
        'monthly_rain': monthly_rain,
        'expected': expected,
        'old_pred': old_pred,
        'old_correct': old_correct,
        'new_pred': new_pred,
        'new_correct': new_correct
    })

# Summary
print('\n' + '='*70)
print('COMPARISON SUMMARY')
print('='*70)

old_correct = sum(1 for r in results if r['old_correct'])
new_correct = sum(1 for r in results if r['new_correct'])
total = len(results)

print(f'\nOld Model v1: {old_correct}/{total} correct ({int(old_correct/total*100)}%)')
print(f'New Model v2: {new_correct}/{total} correct ({int(new_correct/total*100)}%)')

if new_correct > old_correct:
    print(f'\n✅ NEW MODEL IS BETTER! Improvement: +{new_correct-old_correct} tests')
elif new_correct == old_correct:
    print(f'\n⚠️ Same performance')
else:
    print(f'\n❌ Old model was better')

print('\n' + '='*70)
