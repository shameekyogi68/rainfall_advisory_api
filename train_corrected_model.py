#!/usr/bin/env python3
"""
Train New Model with Corrected Labels
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pickle

print('='*70)
print('TRAINING NEW MODEL WITH CORRECTED DATA')
print('='*70)

# Load corrected training data
print('\n1. Loading corrected training data...')
df = pd.read_csv('training_table_v2_CORRECTED.csv')
print(f'   Total samples: {len(df)}')
print(f'   Label distribution:')
print(df['target_category'].value_counts())

# Prepare features and target
print('\n2. Preparing features...')
feature_columns = ['rain_lag_7', 'rain_lag_30', 'rolling_30_rain',
                   'rolling_60_rain', 'rolling_90_rain', 'dry_days_count', 'rain_deficit',  # NEW drought features
                   'temp', 'humidity', 'wind', 'pressure', 'month']

X = df[feature_columns].values
y = df['target_category'].values

print(f'   Features shape: {X.shape}')
print(f'   Target shape: {y.shape}')

# Split data
print('\n3. Splitting train/test sets (80/20)...')
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f'   Training samples: {len(X_train)}')
print(f'   Test samples: {len(X_test)}')

# Train model
print('\n4. Training RandomForest classifier...')
print('   (This may take 1-2 minutes...)')

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42,
    n_jobs=-1,  # Use all CPU cores
    verbose=1
)

model.fit(X_train, y_train)
print('   ✅ Training complete!')

# Evaluate
print('\n5. Evaluating model performance...')
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)

print(f'   Training accuracy: {train_score:.3f} ({train_score*100:.1f}%)')
print(f'   Test accuracy: {test_score:.3f} ({test_score*100:.1f}%)')

# Predictions
y_pred = model.predict(X_test)

print('\n6. Classification Report:')
print(classification_report(y_test, y_pred))

print('\n7. Confusion Matrix:')
print(confusion_matrix(y_test, y_pred))

# Feature importance
print('\n8. Feature Importances:')
for feature, importance in sorted(
    zip(feature_columns, model.feature_importances_),
    key=lambda x: x[1],
    reverse=True
):
    print(f'   {feature:20} : {importance:.4f} ({importance*100:.1f}%)')

# Save model
model_file = 'final_rainfall_classifier_v2_CORRECTED.pkl'
print(f'\n9. Saving model: {model_file}')
with open(model_file, 'wb') as f:
    pickle.dump(model, f)

print('\n' + '='*70)
print('✅ MODEL TRAINING COMPLETE!')
print('='*70)
print(f'\nNew model: {model_file}')
print(f'Test accuracy: {test_score*100:.1f}%')
print('\nNext: Validate on real monsoon dates (Jul 2025, Jun 2025, etc.)')
