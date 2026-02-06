#!/usr/bin/env python3
"""
Test ML Model Against Real Documented Events in Udupi
Ground truth validation using news reports and official records
"""

import pandas as pd
from production_backend import process_advisory_request
from datetime import datetime, timedelta

print('='*70)
print('VALIDATING MODEL AGAINST REAL HISTORICAL EVENTS')
print('='*70)

# Load ground truth events
events = pd.read_csv('udupi_rain_events.csv')
print(f'\n✅ Loaded {len(events)} documented events (2016-2025)')

# Test coordinates (Udupi city center)
lat, lon = 13.3409, 74.7421

# Results storage
results = []

print('\n' + '='*70)
print('TESTING EACH EVENT')
print('='*70)

for idx, event in events.iterrows():
    date_str = event['date']
    event_type = event['event_type']
    expected = event['expected_prediction']
    description = event['description'][:60] + '...' if len(event['description']) > 60 else event['description']
    
    print(f'\n📅 {date_str} - {event_type.upper()}')
    print(f'   Description: {description}')
    print(f'   Expected: {expected}')
    
    # Calculate if date is in valid range (within 1 year of current date)
    event_date = pd.to_datetime(date_str)
    current_date = datetime(2026, 2, 6)  # Current reference date
    
    days_diff = (current_date - event_date).days
    
    # Can only test dates within API's allowed range (<= 10 years in past, <= 30 days future)
    if days_diff > 3650:
        print(f'   ⚠️ SKIPPED: Event is {days_diff} days ago (>10 year limit)')
        results.append({
            'date': date_str,
            'event_type': event_type,
            'expected': expected,
            'prediction': 'N/A',
            'match': None,
            'reason': 'Too old'
        })
        continue
    
    if days_diff < -30:
        print(f'   ⚠️ SKIPPED: Event is {-days_diff} days in future (>30 day limit)')
        results.append({
            'date': date_str,
            'event_type': event_type,
            'expected': expected,
            'prediction': 'N/A',
            'match': None,
            'reason': 'Too far in future'
        })
        continue
    
    # Test the model
    try:
        result = process_advisory_request('ground_truth_test', lat, lon, date_str)
        
        if result['status'] == 'success':
            prediction = result['rainfall']['monthly_prediction']['category']
            confidence = result['rainfall']['monthly_prediction']['confidence_percent']
            forecast_7d = result['rainfall']['next_7_days']['amount_mm']
            
            # Evaluate match
            match = False
            if 'Deficit' in expected and prediction == 'Deficit':
                match = True
            elif 'Excess' in expected and prediction == 'Excess':
                match = True
            elif 'Normal' in expected and prediction == 'Normal':
                match = True
            
            status = '✅ MATCH' if match else '❌ MISS'
            
            print(f'   🤖 Model: {prediction} ({confidence}% confidence)')
            print(f'   📊 7-day forecast: {forecast_7d}mm')
            print(f'   {status}')
            
            results.append({
                'date': date_str,
                'event_type': event_type,
                'expected': expected,
                'prediction': prediction,
                'confidence': confidence,
                'forecast_7d': forecast_7d,
                'match': match,
                'reason': 'Tested'
            })
        else:
            error_msg = result.get('error', {}).get('message', {}).get('en', 'Unknown error')
            print(f'   ❌ ERROR: {error_msg}')
            results.append({
                'date': date_str,
                'event_type': event_type,
                'expected': expected,
                'prediction': 'ERROR',
                'match': False,
                'reason': error_msg
            })
    
    except Exception as e:
        print(f'   ❌ EXCEPTION: {str(e)}')
        results.append({
            'date': date_str,
            'event_type': event_type,
            'expected': expected,
            'prediction': 'EXCEPTION',
            'match': False,
            'reason': str(e)
        })

# Summary
print('\n' + '='*70)
print('VALIDATION SUMMARY')
print('='*70)

results_df = pd.DataFrame(results)

# Overall stats
total = len(results_df)
tested = len(results_df[results_df['reason'] == 'Tested'])
matched = len(results_df[results_df['match'] == True])

print(f'\nTotal Events: {total}')
print(f'Tested: {tested}')
print(f'Matched: {matched}')

if tested > 0:
    accuracy = (matched / tested) * 100
    print(f'\n🎯 ACCURACY: {accuracy:.1f}% ({matched}/{tested})')
else:
    print('\n⚠️ No events could be tested (outside date range)')

# By event type
print('\n📊 BY EVENT TYPE:')
for event_type in results_df['event_type'].unique():
    type_results = results_df[results_df['event_type'] == event_type]
    type_tested = len(type_results[type_results['reason'] == 'Tested'])
    type_matched = len(type_results[type_results['match'] == True])
    
    if type_tested > 0:
        type_acc = (type_matched / type_tested) * 100
        print(f'  {event_type:8}: {type_matched}/{type_tested} ({type_acc:.0f}%)')
    else:
        print(f'  {event_type:8}: Not tested (outside range)')

# Save results
results_df.to_csv('ground_truth_validation_results.csv', index=False)
print(f'\n✅ Results saved: ground_truth_validation_results.csv')

print('\n' + '='*70)
