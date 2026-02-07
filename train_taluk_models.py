#!/usr/bin/env python3
"""
Train Taluk-Level Models
Create separate models for each taluk to capture local patterns
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

print('='*70)
print('TRAINING TALUK-LEVEL MODELS')
print('='*70)

# Load training data
df = pd.read_csv('training_table_v2_CORRECTED.csv')
taluks = df['taluk'].unique()

print(f'\n📍 Found {len(taluks)} taluks: {", ".join(taluks)}')

# Features
feature_columns = ['rain_lag_7', 'rain_lag_30', 'rolling_30_rain',
                   'rolling_60_rain', 'rolling_90_rain', 'dry_days_count', 'rain_deficit',
                   'temp', 'humidity', 'wind', 'pressure', 'month']

models = {}
taluk_stats = []

print('\n' + '='*70)
print('TRAINING EACH TALUK')
print('='*70)

for taluk in sorted(taluks):
    print(f'\n📍 {taluk.upper()}:')
    
    # Filter data for this taluk
    taluk_df = df[df['taluk'] == taluk]
    print(f'   Samples: {len(taluk_df)}')
    
    if len(taluk_df) < 100:
        print(f'   ⚠️  Too few samples, skipping...')
        continue
    
    X = taluk_df[feature_columns].values
    y = taluk_df['target_category'].values
    
    # Split
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    except:
        print(f'   ⚠️  Cannot stratify, using random split')
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    y_pred =model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f'   Train: {len(X_train)}, Test: {len(X_test)}')
    print(f'   Accuracy: {acc*100:.1f}%')
    
    # Store
    models[taluk] = model
    taluk_stats.append({
        'taluk': taluk,
        'samples': len(taluk_df),
        'train': len(X_train),
        'test': len(X_test),
        'accuracy': acc
    })

print('\n' + '='*70)
print('TALUK MODEL SUMMARY')
print('='*70)

stats_df = pd.DataFrame(taluk_stats)
print(stats_df.to_string(index=False))

print(f'\n📊 Overall Stats:')
print(f'   Average accuracy: {stats_df["accuracy"].mean()*100:.1f}%')
print(f'   Best: {stats_df.loc[stats_df["accuracy"].idxmax()]["taluk"]} ({stats_df["accuracy"].max()*100:.1f}%)')
print(f'   Worst: {stats_df.loc[stats_df["accuracy"].idxmin()]["taluk"]} ({stats_df["accuracy"].min()*100:.1f}%)')

# Save all models
print('\n💾 Saving models...')
with open('taluk_models.pkl', 'wb') as f:
    pickle.dump(models, f)

print(f'   ✅ Saved {len(models)} taluk models to: taluk_models.pkl')

# Test on May 2024 Kark ala drought
print('\n' + '='*70)
print('TEST: May 2024 Karkala Drought')
print('='*70)

if 'karkala' in models:
    # Get May 2024 Karkala data
    may_2024_karkala = df[(df['taluk'] == 'karkala') & 
                          (pd.to_datetime(df['date']).dt.year == 2024) &
                          (pd.to_datetime(df['date']).dt.month == 5)]
    
    if len(may_2024_karkala) > 0:
        sample = may_2024_karkala.iloc[0]
        X_test = [sample[feature_columns].values]
        
        pred = models['karkala'].predict(X_test)[0]
        proba = models['karkala'].predict_proba(X_test)[0]
        
        print(f'Karkala-specific model prediction for May 2024:')
        print(f'  Prediction: {pred}')
        print(f'  Probabilities: {dict(zip(models["karkala"].classes_, proba))}')
        print(f'\n  Expected: Deficit (localized drought)')
        if pred == 'Deficit':
            print(f'  ✅ Taluk model captures local drought!')
        else:
            print(f'  ⚠️  Still predicts {pred}')
    else:
        print('No May 2024 Karkala data in training set')
else:
    print('Karkala model not trained')

print('\n' + '='*70)
print('✅ TALUK-LEVEL TRAINING COMPLETE!')
print('='*70)
