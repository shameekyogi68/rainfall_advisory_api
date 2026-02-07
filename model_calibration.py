#!/usr/bin/env python3
"""
Model Calibration for Rainfall Prediction
Calibrates probability outputs using Platt scaling
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from datetime import datetime

def load_data_and_split():
    """Load training data and create validation split"""
    print("Loading data...")
    
    # Load monthly targets (corrected labels)
    df = pd.read_csv('rainfall_monthly_targets_v2_CORRECTED.csv')
    
    # Load daily historical data for features
    daily_df = pd.read_csv('rainfall_daily_historical_v1.csv')
    daily_df['date'] = pd.to_datetime(daily_df['date'], format='mixed')
    
    # Merge to create features (simplified - just get the data we have)
    # We'll use the precomputed features from the model training
    
    # Actually, let's just load from the exact same way the model was trained
    # Check if we have the feature-engineered dataset
    import os
    if os.path.exists('engineered_features.csv'):
        df = pd.read_csv('engineered_features.csv')
    else:
        print("  Note: Using monthly targets, will calibrate on model's probability outputs")
        # We can still calibrate using just predictions on validation set
        df = pd.read_csv('rainfall_monthly_targets_v2_CORRECTED.csv')
    
    # Feature columns (must match training)
    feature_columns = [
        'rain_lag_7', 'rain_lag_30', 'rolling_30_rain', 'rolling_60_rain',
        'rolling_90_rain', 'dry_days_count', 'rain_deficit',
        'temp', 'humidity', 'wind_speed', 'pressure', 'month'
    ]
    
    # Check if features exist
    available_features = [col for col in feature_columns if col in df.columns]
    
    if len(available_features) < 5:
        print(f"  ⚠ Warning: Only {len(available_features)} features found")
        print("  Will use simple calibration method instead")
        return None, None, None, None, None
    
    X = df[available_features]
    y = df['label'] if 'label' in df.columns else df['category_encoded']
    
    # Temporal split (last 20% for calibration)
    split_idx = int(len(df) * 0.8)
    X_train = X[:split_idx]
    X_val = X[split_idx:]
    y_train = y[:split_idx]
    y_val = y[split_idx:]
    
    print(f"Train: {len(X_train)}, Validation: {len(X_val)}")
    print(f"Features: {len(available_features)}")
    
    return X_train, X_val, y_train, y_val, available_features

def calibrate_model(model_path, X_val, y_val):
    """Calibrate existing model using Platt scaling"""
    print(f"\nLoading model: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print("Calibrating model with Platt scaling...")
    
    # Calibrate using sigmoid (Platt scaling)
    calibrated_model = CalibratedClassifierCV(
        model, 
        method='sigmoid',  # Platt scaling
        cv='prefit'  # Use pre-fitted model
    )
    
    # Fit calibration on validation set
    calibrated_model.fit(X_val, y_val)
    
    print("✓ Calibration complete")
    
    return calibrated_model

def evaluate_calibration(original_model, calibrated_model, X_val, y_val):
    """Compare calibration before and after"""
    print("\n" + "="*70)
    print("CALIBRATION EVALUATION")
    print("="*70)
    
    # Get predictions
    orig_probs = original_model.predict_proba(X_val)
    cal_probs = calibrated_model.predict_proba(X_val)
    
    # For each confidence bin, check actual accuracy
    bins = np.linspace(0, 1, 11)  # 0-10%, 10-20%, ..., 90-100%
    
    print("\nCalibration Curve (Deficit class):")
    print(f"{'Predicted %':<15} {'Before (Actual %)':<20} {'After (Actual %)':<20} {'Improvement'}")
    print("-" * 70)
    
    for i in range(len(bins)-1):
        lower, upper = bins[i], bins[i+1]
        
        # Original model
        mask_orig = (orig_probs[:, 0] >= lower) & (orig_probs[:, 0] < upper)
        if mask_orig.sum() > 0:
            actual_orig = (y_val[mask_orig] == 0).mean()
        else:
            actual_orig = np.nan
        
        # Calibrated model
        mask_cal = (cal_probs[:, 0] >= lower) & (cal_probs[:, 0] < upper)
        if mask_cal.sum() > 0:
            actual_cal = (y_val[mask_cal] == 0).mean()
        else:
            actual_cal = np.nan
        
        if not np.isnan(actual_orig) and not np.isnan(actual_cal):
            improvement = abs(actual_cal - (lower+upper)/2) - abs(actual_orig - (lower+upper)/2)
            improvement_str = f"{improvement:+.1%}" if improvement < 0 else f"BETTER {improvement:+.1%}"
            
            print(f"{int(lower*100):>2}-{int(upper*100):>2}%     "
                  f"{actual_orig:>6.1%} (n={mask_orig.sum():<4})  "
                  f"{actual_cal:>6.1%} (n={mask_cal.sum():<4})  "
                  f"{improvement_str}")
    
    # Overall metrics
    orig_pred = original_model.predict(X_val)
    cal_pred = calibrated_model.predict(X_val)
    
    orig_acc = (orig_pred == y_val).mean()
    cal_acc = (cal_pred == y_val).mean()
    
    print("\n" + "="*70)
    print(f"Overall Accuracy:")
    print(f"  Before: {orig_acc:.1%}")
    print(f"  After:  {cal_acc:.1%}")
    print(f"  Change: {cal_acc - orig_acc:+.1%}")
    print("="*70)

def plot_calibration_curve(original_model, calibrated_model, X_val, y_val):
    """Plot calibration curve"""
    from sklearn.calibration import calibration_curve
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # For Deficit class (index 0)
    orig_probs = original_model.predict_proba(X_val)[:, 0]
    cal_probs = calibrated_model.predict_proba(X_val)[:, 0]
    
    y_binary = (y_val == 0).astype(int)
    
    # Original
    fraction_orig, mean_pred_orig = calibration_curve(y_binary, orig_probs, n_bins=10)
    ax1.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
    ax1.plot(mean_pred_orig, fraction_orig, 's-', label='Original model')
    ax1.set_xlabel('Predicted probability')
    ax1.set_ylabel('Actual probability')
    ax1.set_title('Before Calibration')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Calibrated
    fraction_cal, mean_pred_cal = calibration_curve(y_binary, cal_probs, n_bins=10)
    ax2.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
    ax2.plot(mean_pred_cal, fraction_cal, 's-', color='green', label='Calibrated model')
    ax2.set_xlabel('Predicted probability')
    ax2.set_ylabel('Actual probability')
    ax2.set_title('After Calibration')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('calibration_curve.png', dpi=150)
    print("\n✓ Calibration curve saved: calibration_curve.png")

def calibrate_all_models():
    """Calibrate district and taluk models"""
    print("\n" + "="*70)
    print("MODEL CALIBRATION PIPELINE")
    print("="*70)
    
    # Load data
    X_train, X_val, y_train, y_val, feature_cols = load_data_and_split()
    
    # 1. Calibrate district model
    print("\n[1/2] Calibrating District Model")
    print("-" * 70)
    
    orig_model = pickle.load(open('final_rainfall_classifier_v1.pkl', 'rb'))
    cal_district = calibrate_model('final_rainfall_classifier_v1.pkl', X_val, y_val)
    
    # Evaluate
    evaluate_calibration(orig_model, cal_district, X_val, y_val)
    
    # Plot
    plot_calibration_curve(orig_model, cal_district, X_val, y_val)
    
    # Save
    with open('calibrated_district_model.pkl', 'wb') as f:
        pickle.dump(cal_district, f)
    print("\n✓ Saved: calibrated_district_model.pkl")
    
    # 2. Calibrate taluk models
    print("\n[2/2] Calibrating Taluk Models")
    print("-" * 70)
    
    try:
        taluk_models = pickle.load(open('taluk_models.pkl', 'rb'))
        calibrated_taluk_models = {}
        
        for taluk_name, model in taluk_models.items():
            print(f"\n  Calibrating {taluk_name}...")
            
            # Filter validation data for this taluk
            df_full = pd.read_csv('corrected_rainfall_data.csv')
            taluk_val = df_full[df_full['taluk'] == taluk_name].tail(int(len(df_full)*0.2))
            
            if len(taluk_val) > 50:  # Need enough data for calibration
                X_taluk = taluk_val[feature_cols]
                y_taluk = taluk_val['label']
                
                cal_model = CalibratedClassifierCV(model, method='sigmoid', cv='prefit')
                cal_model.fit(X_taluk, y_taluk)
                
                calibrated_taluk_models[taluk_name] = cal_model
                print(f"    ✓ {taluk_name} calibrated")
            else:
                calibrated_taluk_models[taluk_name] = model  # Keep original
                print(f"    ⚠ {taluk_name} - insufficient data, keeping original")
        
        # Save
        with open('calibrated_taluk_models.pkl', 'wb') as f:
            pickle.dump(calibrated_taluk_models, f)
        print("\n✓ Saved: calibrated_taluk_models.pkl")
        
    except FileNotFoundError:
        print("  ⚠ taluk_models.pkl not found, skipping")
    
    print("\n" + "="*70)
    print("✓ CALIBRATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Review calibration_curve.png")
    print("2. Update production_backend.py to use calibrated models")
    print("3. Test with real predictions")

if __name__ == '__main__':
    calibrate_all_models()
