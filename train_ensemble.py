#!/usr/bin/env python3
"""
Train Ensemble Model: RandomForest + XGBoost
Combines multiple models for better accuracy
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

print('='*70)
print('TRAINING ENSEMBLE MODEL (RandomForest + XGBoost)')
print('='*70)

# Load training data
print('\n1. Loading training data...')
df = pd.read_csv('training_table_v2_CORRECTED.csv')
print(f'   Total samples: {len(df)}')

# Prepare features
print('\n2. Preparing features...')
feature_columns = ['rain_lag_7', 'rain_lag_30', 'rolling_30_rain',
                   'rolling_60_rain', 'rolling_90_rain', 'dry_days_count', 'rain_deficit',
                   'temp', 'humidity', 'wind', 'pressure', 'month']

X = df[feature_columns].values
y = df['target_category'].values

# Split
print('\n3. Splitting train/test...')
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train RandomForest
print('\n4. Training RandomForest...')
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_proba = rf_model.predict_proba(X_test)
rf_acc = accuracy_score(y_test, rf_pred)
print(f'   RandomForest accuracy: {rf_acc:.3f} ({rf_acc*100:.1f}%)')

# Train XGBoost
print('\n5. Training XGBoost...')
xgb_model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    n_jobs=-1
)
xgb_model.fit(X_train, y_train)
xgb_pred = xgb_model.predict(X_test)
xgb_proba = xgb_model.predict_proba(X_test)
xgb_acc = accuracy_score(y_test, xgb_pred)
print(f'   XGBoost accuracy: {xgb_acc:.3f} ({xgb_acc*100:.1f}%)')

# Ensemble: Average probabilities
print('\n6. Creating ensemble (average probabilities)...')
ensemble_proba = (rf_proba + xgb_proba) / 2
ensemble_pred = [rf_model.classes_[i] for i in ensemble_proba.argmax(axis=1)]
ensemble_acc = accuracy_score(y_test, ensemble_pred)
print(f'   Ensemble accuracy: {ensemble_acc:.3f} ({ensemble_acc*100:.1f}%)')

# Compare
print('\n7. Model Comparison:')
print(f'   RandomForest: {rf_acc*100:.1f}%')
print(f'   XGBoost:      {xgb_acc*100:.1f}%')
print(f'   Ensemble:     {ensemble_acc*100:.1f}%')

if ensemble_acc > max(rf_acc, xgb_acc):
    print(f'\n   ✅ Ensemble wins! (+{(ensemble_acc - max(rf_acc, xgb_acc))*100:.1f}%)')
    best_model = 'ensemble'
elif xgb_acc > rf_acc:
    print(f'\n   ✅ XGBoost wins! (+{(xgb_acc - rf_acc)*100:.1f}%)')
    best_model = 'xgboost'
else:
    print(f'\n   ✅ RandomForest wins!')
    best_model = 'randomforest'

# Detailed report for best model
print('\n8. Detailed Classification Report (Ensemble):')
print(classification_report(y_test, ensemble_pred))

# Save both models for ensemble
print('\n9. Saving models...')
with open('model_randomforest.pkl', 'wb') as f:
    pickle.dump(rf_model, f)
    
with open('model_xgboost.pkl', 'wb') as f:
    pickle.dump(xgb_model, f)

# Save ensemble config
ensemble_config = {
    'models': ['randomforest', 'xgboost'],
    'weights': [0.5, 0.5],
    'accuracy': ensemble_acc,
    'best_single': best_model
}

with open('ensemble_config.pkl', 'wb') as f:
    pickle.dump(ensemble_config, f)

print(f'\n✅ Models saved!')
print(f'   - model_randomforest.pkl')
print(f'   - model_xgboost.pkl')
print(f'   - ensemble_config.pkl')

print('\n' + '='*70)
print(f'✅ ENSEMBLE TRAINING COMPLETE!')
print(f'Best accuracy: {max(rf_acc, xgb_acc, ensemble_acc)*100:.1f}%')
print('='*70)
