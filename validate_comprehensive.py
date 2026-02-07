#!/usr/bin/env python3
"""
Comprehensive Validation on 2025-2026 Verified Events
Test model against recent documented events with citations
"""

import pandas as pd
from production_backend import process_advisory_request
from datetime import datetime, timedelta

print('='*70)
print('COMPREHENSIVE VALIDATION: 2025-2026 VERIFIED EVENTS')
print('='*70)

# Load both event datasets
old_events = pd.read_csv('udupi_rain_events.csv')
new_events = pd.read_csv('udupi_events_2025_2026.csv')

print(f'\n📚 Event Sources:')
print(f'   Historical (2016-2025): {len(old_events)} events')
print(f'   Recent (2025-2026): {len(new_events)} events')
print(f'   Total: {len(old_events) + len(new_events)} events')

# Test coordinates
lat, lon = 13.3409, 74.7421

# Results storage
all_results = []

# Test old events first
print('\n' + '='*70)
print('TESTING HISTORICAL EVENTS (2016-2025)')
print('='*70)

for idx, event in old_events.iterrows():
    date_str = event['date']
    event_type = event['event_type']
    expected = event['expected_prediction']
    
    result = process_advisory_request('validation', lat, lon, date_str)
    
    if result['status'] == 'success':
        pred = result['rainfall']['monthly_prediction']['category']
        conf = result['rainfall']['monthly_prediction']['confidence_percent']
        
        match = False
        if 'Deficit' in expected and pred == 'Deficit':
            match = True
        elif 'Excess' in expected and pred == 'Excess':
            match = True
        elif 'Normal' in expected and pred == 'Normal':
            match = True
        
        status = '✅' if match else '❌'
        print(f'{date_str} ({event_type:8}): {pred:8} ({conf}%) {status}')
        
        all_results.append({
            'date': date_str,
            'event_type': event_type,
            'expected': expected,
            'prediction': pred,
            'confidence': conf,
            'match': match,
            'testable': True
        })
    else:
        error = result.get('error', {}).get('message', {}).get('en', 'Unknown')
        if 'not enough data' in error.lower():
            print(f'{date_str} ({event_type:8}): ⚠️  No data')
            all_results.append({
                'date': date_str,
                'event_type': event_type,
                'expected': expected,
                'prediction': 'NO_DATA',
                'match': False,
                'testable': False
            })
        else:
            print(f'{date_str} ({event_type:8}): ❌ {error}')

# Test new 2025-2026 events
print('\n' + '='*70)
print('TESTING NEW VERIFIED EVENTS (2025-2026)')
print('='*70)

for idx, event in new_events.iterrows():
    # Use middle date if range
    date_start = event['date_start']
    date_end = event['date_end']
    event_type = event['event_type']
    expected = event['expected_prediction']
    desc = event['description'][:50]
    
    # Test on the end date (when event is complete)
    test_date = date_end
    
    print(f'\n📅 {test_date} - {event_type.upper()}')
    print(f'   {desc}...')
    
    result = process_advisory_request('validation', lat, lon, test_date)
    
    if result['status'] == 'success':
        pred = result['rainfall']['monthly_prediction']['category']
        conf = result['rainfall']['monthly_prediction']['confidence_percent']
        
        match = pred == expected
        status = '✅ CORRECT' if match else '❌ MISS'
        
        print(f'   Expected: {expected:8}')
        print(f'   Model:    {pred:8} ({conf}%) {status}')
        
        all_results.append({
            'date': test_date,
            'event_type': event_type,
            'expected': expected,
            'prediction': pred,
            'confidence': conf,
            'match': match,
            'testable': True
        })
    else:
        error = result.get('error', {}).get('message', {}).get('en', 'Unknown')
        print(f'   ❌ ERROR: {error}')
        all_results.append({
            'date': test_date,
            'event_type': event_type,
            'expected': expected,
            'prediction': 'ERROR',
            'match': False,
            'testable': False
        })

# Final summary
print('\n' + '='*70)
print('FINAL VALIDATION SUMMARY')
print('='*70)

results_df = pd.DataFrame(all_results)

total = len(results_df)
testable = len(results_df[results_df['testable'] == True])
correct = len(results_df[results_df['match'] == True])

print(f'\nTotal Events: {total}')
print(f'Testable: {testable}')
print(f'Correct: {correct}')

if testable > 0:
    accuracy = (correct / testable) * 100
    print(f'\n🎯 MODEL ACCURACY: {accuracy:.1f}% ({correct}/{testable})')
    
    if accuracy >= 95:
        print('✅ 95% ACCURACY TARGET ACHIEVED!')
    elif accuracy >= 90:
        print('✅ 90% ACCURACY ACHIEVED - Close to target!')
    elif accuracy >= 85:
        print('⚠️  85%+ ACCURACY - Good, room for improvement')
    else:
        print('⚠️  Below 85% - Needs improvement')

# By event type
print('\n📊 ACCURACY BY EVENT TYPE:')
for event_type in results_df['event_type'].unique():
    type_results = results_df[results_df['event_type'] == event_type]
    type_testable = len(type_results[type_results['testable'] == True])
    type_correct = len(type_results[type_results['match'] == True])
    
    if type_testable > 0:
        type_acc = (type_correct / type_testable) * 100
        print(f'  {event_type:15}: {type_correct}/{type_testable} ({type_acc:.0f}%)')

# Save results
results_df.to_csv('comprehensive_validation_results.csv', index=False)
print(f'\n✅ Results saved: comprehensive_validation_results.csv')

print('\n' + '='*70)
