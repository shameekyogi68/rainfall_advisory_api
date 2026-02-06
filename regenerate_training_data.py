#!/usr/bin/env python3
"""
Regenerate Training Data with Correct Labels
"""

import pandas as pd
import numpy as np
from correct_labeling import label_monthly_rainfall

print('='*70)
print('REGENERATING TRAINING DATA WITH CORRECT LABELS')
print('='*70)

# Load historical rainfall data
print('\n1. Loading historical data...')
rainfall_df = pd.read_csv('rainfall_daily_historical_v1.csv')
rainfall_df['date'] = pd.to_datetime(rainfall_df['date'], format='mixed')

weather_df = pd.read_csv('weather_drivers_daily_v1.csv')
weather_df['date'] = pd.to_datetime(weather_df['date'], format='mixed')

print(f'   Rainfall data: {len(rainfall_df)} rows')
print(f'   Weather data: {len(weather_df)} rows')

# Calculate monthly targets with CORRECT labels
print('\n2. Calculating monthly rainfall totals...')
rainfall_df['year'] = rainfall_df['date'].dt.year
rainfall_df['month'] = rainfall_df['date'].dt.month

monthly_totals = rainfall_df.groupby(['taluk', 'year', 'month'])['rainfall'].sum().reset_index()
monthly_totals.columns = ['taluk', 'year', 'month', 'monthly_rainfall']

# Apply CORRECT labeling
print('\n3. Applying meteorologically correct labels...')

def apply_correct_label(row):
    return label_monthly_rainfall(row['month'], row['monthly_rainfall'], row['taluk'])

monthly_totals['target_category'] = monthly_totals.apply(apply_correct_label, axis=1)

# Save corrected monthly targets
monthly_targets_file = 'rainfall_monthly_targets_v2_CORRECTED.csv'
monthly_totals.to_csv(monthly_targets_file, index=False)
print(f'   Saved: {monthly_targets_file}')

# Display label distribution
print('\n4. New label distribution by month:')
label_dist = monthly_totals.groupby(['month', 'target_category']).size().unstack(fill_value=0)
print(label_dist)

# Create training table
print('\n5. Creating training table...')

# For each daily record, add features and monthly target
training_data = []

for taluk in rainfall_df['taluk'].unique():
    print(f'   Processing {taluk}...')
    
    taluk_rainfall = rainfall_df[rainfall_df['taluk'] == taluk].sort_values('date')
    taluk_weather = weather_df[weather_df['taluk'] == taluk].sort_values('date')
    
    # Merge rainfall and weather
    merged = pd.merge(taluk_rainfall, taluk_weather, on=['date', 'taluk'], how='inner')
    
    for idx, row in merged.iterrows():
        date = row['date']
        
        # Skip if we don't have enough history (need 30 days)
        if date < merged['date'].min() + pd.Timedelta(days=30):
            continue
        
        # Get historical data before this date
        hist = merged[merged['date'] < date].tail(30)
        
        if len(hist) < 30:
            continue
        
        # Compute lag features (original)
        rain_lag_7 = hist.iloc[-7]['rainfall']
        rain_lag_30 = hist.iloc[0]['rainfall'] 
        rolling_30_rain = hist['rainfall'].sum()
        
        # NEW: Drought-specific features
        rolling_60_rain = hist.tail(60)['rainfall'].sum() if len(hist) >= 60 else hist['rainfall'].sum()
        rolling_90_rain = hist.tail(90)['rainfall'].sum() if len(hist) >= 90 else hist['rainfall'].sum()
        dry_days_count = (hist.tail(30)['rainfall'] < 2).sum()  # Days with < 2mm rain
        
        # Calculate deficit vs historical average for this month
        month = date.month
        year = date.year
        hist_same_month = merged[(merged['date'].dt.month == month) & (merged['date'].dt.year < year)]
        if len(hist_same_month) > 0:
            avg_monthly = hist_same_month.groupby(hist_same_month['date'].dt.year)['rainfall'].sum().mean()
            rain_deficit = rolling_30_rain - (avg_monthly / 30 * 30)  # Deficit from normal
        else:
            rain_deficit = 0
        
        # Get month/year for monthly target
        month = date.month
        year = date.year
        
        # Find monthly target from corrected data
        monthly_target = monthly_totals[
            (monthly_totals['taluk'] == taluk) &
            (monthly_totals['year'] == year) &
            (monthly_totals['month'] == month)
        ]
        
        if len(monthly_target) == 0:
            continue
        
        monthly_rain = monthly_target.iloc[0]['monthly_rainfall']
        target_category = monthly_target.iloc[0]['target_category']
        
        # Create training row with NEW features
        training_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'taluk': taluk,
            'rain_lag_7': rain_lag_7,
            'rain_lag_30': rain_lag_30,
            'rolling_30_rain': rolling_30_rain,
            'rolling_60_rain': rolling_60_rain,  # NEW
            'rolling_90_rain': rolling_90_rain,  # NEW
            'dry_days_count': dry_days_count,    # NEW
            'rain_deficit': rain_deficit,        # NEW
            'temp': row['temp'],
            'humidity': row['humidity'],
            'wind': row['wind'],
            'pressure': row['pressure'],
            'month': month,
            'target_monthly_rain': monthly_rain,
            'target_category': target_category
        })

# Convert to DataFrame
training_df = pd.DataFrame(training_data)

print(f'\n6. Created {len(training_df)} training samples')

# Check label distribution
print('\nLabel distribution in training data:')
print(training_df['target_category'].value_counts())
print('\nPercentages:')
print(training_df['target_category'].value_counts(normalize=True) * 100)

# Save corrected training data
training_file = 'training_table_v2_CORRECTED.csv'
training_df.to_csv(training_file, index=False)
print(f'\n✅ Saved corrected training data: {training_file}')

# Verify key fixes
print('\n' + '='*70)
print('VERIFICATION: Checking previously wrong labels')
print('='*70)

# Check February 2020 (was wrongly Excess)
feb_2020 = training_df[(training_df['date'].str.startswith('2020-02'))]
if len(feb_2020) > 0:
    feb_label = feb_2020.iloc[0]['target_category']
    feb_rain = feb_2020.iloc[0]['target_monthly_rain']
    print(f'Feb 2020: {feb_rain:.2f}mm → {feb_label} (was wrongly "Excess")')
    
# Check July 2025 (was wrongly Normal for heavy rain)
jul_2025 = training_df[(training_df['date'].str.startswith('2025-07'))]
if len(jul_2025) > 0:
    jul_label = jul_2025.iloc[0]['target_category']
    jul_rain = jul_2025.iloc[0]['target_monthly_rain']
    print(f'Jul 2025: {jul_rain:.2f}mm → {jul_label} (should be Normal/Excess)')

print('\n✅ Training data regeneration complete!')
