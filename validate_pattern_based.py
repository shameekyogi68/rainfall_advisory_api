#!/usr/bin/env python3
"""
Forward Validation: Pattern-Based Climatological Testing
Tests model behavior against expected seasonal patterns for 2026-2027
"""

import pandas as pd
from production_backend import process_advisory_request
from datetime import datetime

print('='*70)
print('FORWARD VALIDATION: CLIMATOLOGICAL PATTERN TESTING')
print('='*70)

# Load pattern-based test windows
patterns = pd.read_csv('pattern_based_validation_2026_2027.csv')
print(f'\n📅 Testing {len(patterns)} pattern-based windows (2026-2027)')

lat, lon = 13.3409, 74.7421

results = []
seasonal_performance = {
    'dry': {'total': 0, 'correct': 0},
    'monsoon': {'total': 0, 'correct': 0},
    'transition': {'total': 0, 'correct': 0}
}

print('\n' + '='*70)
print('PATTERN-BY-PATTERN VALIDATION')
print('='*70)

for idx, pattern in patterns.iterrows():
    date = pattern['date']
    event_type = pattern['event_type']
    expected = pattern['expected_behavior']
    basis = pattern['climatology_basis']
    test_use = pattern['ml_test_use']
    
    print(f'\n📅 {date} - {event_type.upper()}')
    print(f'   Pattern: {basis}')
    print(f'   Expected: {expected}')
    print(f'   Test Use: {test_use}')
    
    try:
        result = process_advisory_request('pattern_test', lat, lon, date)
        
        if result['status'] == 'success':
            pred = result['rainfall']['monthly_prediction']['category']
            conf = result['rainfall']['monthly_prediction']['confidence_percent']
            
            # Check if prediction aligns with expected climatological behavior
            if 'or' in expected:
                # Multiple acceptable predictions
                acceptable = expected.split(' or ')
                match = pred in acceptable
            else:
                match = pred == expected
            
            # Categorize season
            if 'dry' in event_type or 'deficit' in event_type:
                season = 'dry'
            elif 'monsoon' in event_type or 'flood' in event_type or 'extreme' in event_type:
                season = 'monsoon'
            else:
                season = 'transition'
            
            seasonal_performance[season]['total'] += 1
            if match:
                seasonal_performance[season]['correct'] += 1
            
            status = '✅ ALIGNED' if match else '❌ MISALIGNED'
            print(f'   Model: {pred} ({conf}%)')
            print(f'   {status}')
            
            results.append({
                'date': date,
                'event_type': event_type,
                'expected': expected,
                'prediction': pred,
                'confidence': conf,
                'aligned': match,
                'season': season,
                'test_use': test_use
            })
        else:
            error = result.get('error', {}).get('message', {}).get('en', 'Unknown')
            print(f'   ⚠️ Cannot test: {error}')
            results.append({
                'date': date,
                'event_type': event_type,
                'expected': expected,
                'prediction': 'ERROR',
                'aligned': False,
                'season': 'unknown',
                'test_use': test_use
            })
    except Exception as e:
        print(f'   ❌ Error: {str(e)}')

# Summary
print('\n' + '='*70)
print('CLIMATOLOGICAL PATTERN ALIGNMENT SUMMARY')
print('='*70)

results_df = pd.DataFrame(results)
testable = results_df[results_df['prediction'] != 'ERROR']

if len(testable) > 0:
    total = len(testable)
    aligned = len(testable[testable['aligned'] == True])
    accuracy = (aligned / total) * 100
    
    print(f'\nTotal Patterns Tested: {total}')
    print(f'Climatologically Aligned: {aligned}')
    print(f'\n🎯 PATTERN ALIGNMENT: {accuracy:.1f}% ({aligned}/{total})')
    
    # Seasonal breakdown
    print('\n📊 BY SEASON:')
    for season, stats in seasonal_performance.items():
        if stats['total'] > 0:
            season_acc = (stats['correct'] / stats['total']) * 100
            print(f'  {season.capitalize():12}: {stats["correct"]}/{stats["total"]} ({season_acc:.0f}%)')
    
    # False alarm check (dry season)
    dry_patterns = testable[testable['season'] == 'dry']
    if len(dry_patterns) > 0:
        false_alarms = len(dry_patterns[(dry_patterns['prediction'] == 'Excess')])
        print(f'\n⚠️ FALSE ALARM CHECK (Dry Season):')
        print(f'  Dry periods tested: {len(dry_patterns)}')
        print(f'  False Excess predictions: {false_alarms}')
        if false_alarms == 0:
            print(f'  ✅ No false alarms!')
        else:
            print(f'  ⚠️ {false_alarms} false alarm(s) detected')
    
    # Monsoon detection
    monsoon_patterns = testable[testable['season'] == 'monsoon']
    if len(monsoon_patterns) > 0:
        correct_monsoon = len(monsoon_patterns[monsoon_patterns['aligned'] == True])
        monsoon_acc = (correct_monsoon / len(monsoon_patterns)) * 100
        print(f'\n☔ MONSOON DETECTION:')
        print(f'  Monsoon patterns tested: {len(monsoon_patterns)}')
        print(f'  Correctly detected: {correct_monsoon}/{len(monsoon_patterns)} ({monsoon_acc:.0f}%)')

# Save results
results_df.to_csv('pattern_validation_results_2026_2027.csv', index=False)
print(f'\n✅ Results saved: pattern_validation_results_2026_2027.csv')

print('\n' + '='*70)
print('NOTE: These are pattern-based projections, not actual events')
print('Use for: seasonal awareness, false alarm control, regime detection')
print('='*70)
