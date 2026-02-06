#!/usr/bin/env python3
"""
Correct Rainfall Labeling Logic for Udupi District
Based on meteorological patterns and seasonal variations
"""

import pandas as pd

def label_monthly_rainfall(month, monthly_rainfall_mm, taluk='udupi'):
    """
    Correctly label monthly rainfall based on season and meteorological norms.
    
    Args:
        month: Month number (1-12)
        monthly_rainfall_mm: Total rainfall in month (mm)
        taluk: Taluk name (default: udupi)
    
    Returns:
        'Deficit', 'Normal', or 'Excess'
    """
    
    # Udupi district rainfall patterns (based on historical averages)
    # Source: IMD data and our historical analysis
    
    if month in [1, 2]:  # January, February - DRY SEASON
        # Historical avg: 1-5mm/month
        if monthly_rainfall_mm < 10:
            return 'Deficit'
        elif monthly_rainfall_mm < 30:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 3:  # March - Late Dry Season
        # Historical avg: 10-20mm/month
        if monthly_rainfall_mm < 20:
            return 'Deficit'
        elif monthly_rainfall_mm < 40:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 4:  # April - Pre-Monsoon Transition
        # Historical avg: 50-80mm/month
        if monthly_rainfall_mm < 40:
            return 'Deficit'
        elif monthly_rainfall_mm < 90:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 5:  # May - Pre-Monsoon
        # Historical avg: 200-400mm/month
        if monthly_rainfall_mm < 150:
            return 'Deficit'
        elif monthly_rainfall_mm < 450:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 6:  # June - SW Monsoon Start
        # Historical avg: 700-1100mm/month
        if monthly_rainfall_mm < 600:
            return 'Deficit'
        elif monthly_rainfall_mm < 1200:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 7:  # July - Peak SW Monsoon
        # Historical avg: 1200-1700mm/month
        if monthly_rainfall_mm < 1000:
            return 'Deficit'
        elif monthly_rainfall_mm < 1800:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 8:  # August - SW Monsoon
        # Historical avg: 700-1200mm/month
        if monthly_rainfall_mm < 600:
            return 'Deficit'
        elif monthly_rainfall_mm < 1300:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 9:  # September - Late Monsoon
        # Historical avg: 200-500mm/month
        if monthly_rainfall_mm < 200:
            return 'Deficit'
        elif monthly_rainfall_mm < 600:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 10:  # October - Monsoon Retreat
        # Historical avg: 150-300mm/month
        if monthly_rainfall_mm < 120:
            return 'Deficit'
        elif monthly_rainfall_mm < 350:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 11:  # November - Post-Monsoon
        # Historical avg: 50-150mm/month
        if monthly_rainfall_mm < 40:
            return 'Deficit'
        elif monthly_rainfall_mm < 180:
            return 'Normal'
        else:
            return 'Excess'
    
    elif month == 12:  # December - Dry Season Returns
        # Historical avg: 10-50mm/month
        if monthly_rainfall_mm < 15:
            return 'Deficit'
        elif monthly_rainfall_mm < 60:
            return 'Normal'
        else:
            return 'Excess'
    
    else:
        raise ValueError(f"Invalid month: {month}")


def test_labeling_logic():
    """Test the labeling function on known data"""
    
    test_cases = [
        # (month, rainfall, expected_label, description)
        (2, 3.77, 'Deficit', 'Feb 2020 - was wrongly labeled Excess'),
        (7, 1590, 'Normal', 'Jul 2025 - heavy monsoon'),
        (7, 1877, 'Excess', 'Jul 2023 - very heavy monsoon'),
        (6, 1063, 'Normal', 'Jun 2025 - monsoon'),
        (8, 1276, 'Normal', 'Aug 2025 - monsoon'),
        (1, 1.29, 'Deficit', 'Jan 2020 - dry'),
        (5, 316, 'Normal', 'May - pre-monsoon'),
        (12, 32, 'Normal', 'Dec - dry season'),
    ]
    
    print('='*70)
    print('TESTING NEW LABELING LOGIC')
    print('='*70)
    
    correct = 0
    total = len(test_cases)
    
    for month, rainfall, expected, description in test_cases:
        result = label_monthly_rainfall(month, rainfall)
        is_correct = (result == expected)
        correct += is_correct
        
        status = '✅' if is_correct else '❌'
        print(f'{status} Month {month:2}, {rainfall:7.1f}mm → {result:7} (expected {expected:7}) - {description}')
    
    print(f'\n{correct}/{total} tests passed ({int(correct/total*100)}%)')
    return correct == total


if __name__ == '__main__':
    success = test_labeling_logic()
    if success:
        print('\n✅ All labeling tests passed! Ready to use.')
    else:
        print('\n❌ Some tests failed. Review thresholds.')
