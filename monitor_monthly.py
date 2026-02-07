#!/usr/bin/env python3
"""
Continuous Monitoring Script for 2026-2027
Run monthly to validate model against climatological patterns
"""

import pandas as pd
from datetime import datetime, timedelta
from production_backend import process_advisory_request

def monitor_current_month():
    """Monitor model predictions for current month against expected patterns"""
    
    # Load pattern expectations
    patterns = pd.read_csv('pattern_based_validation_2026_2027.csv')
    patterns['window_start'] = pd.to_datetime(patterns['window_start'])
    patterns['window_end'] = pd.to_datetime(patterns['window_end'])
    
    today = datetime.now()
    lat, lon = 13.3409, 74.7421
    
    print('='*70)
    print(f'MONTHLY MONITORING: {today.strftime("%B %Y")}') 
    print('='*70)
    
    # Find applicable pattern windows
    current_patterns = patterns[
        (patterns['window_start'] <= today) &
        (patterns['window_end'] >= today)
    ]
    
    if len(current_patterns) == 0:
        print(f'\nNo climatological pattern windows for {today.strftime("%B %Y")}')
        print('Model behavior: No specific expectations this period')
        return
    
    print(f'\n📅 Active Pattern Windows: {len(current_patterns)}')
    
    for _, pattern in current_patterns.iterrows():
        print(f'\n{pattern["event_type"].upper()}:')
        print(f'  Window: {pattern["window_start"].strftime("%b %d")} - {pattern["window_end"].strftime("%b %d")}')
        print(f'  Expected: {pattern["expected_behavior"]}')
        print(f'  Basis: {pattern["climatology_basis"]}')
        
        # Test model
        test_date = today.strftime('%Y-%m-%d')
        result = process_advisory_request('monitor', lat, lon, test_date)
        
        if result['status'] == 'success':
            pred = result['rainfall']['monthly_prediction']['category']
            conf = result['rainfall']['monthly_prediction']['confidence_percent']
            
            # Check alignment
            if 'or' in pattern['expected_behavior']:
                acceptable = pattern['expected_behavior'].split(' or ')
                aligned = pred in acceptable
            else:
                aligned = pred == pattern['expected_behavior']
            
            status = '✅ ALIGNED' if aligned else '⚠️ MISALIGNED'
            
            print(f'  Model Prediction: {pred} ({conf}%)')
            print(f'  {status}')
            
            # Alert if misaligned
            if not aligned:
                print(f'  🚨 ALERT: Prediction does not match climatological expectation!')
                print(f'  Action: Review model or update climatology expectations')
        else:
            print(f'  ❌ Cannot test: Model error')
    
    print('\n' + '='*70)
    print('TIP: Run this script monthly to track pattern alignment')
    print('='*70)

if __name__ == '__main__':
    monitor_current_month()
