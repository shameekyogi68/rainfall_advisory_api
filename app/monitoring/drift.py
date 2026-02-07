import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from scipy import stats
import os
from ..config import settings
BASE_DIR = Path(settings.BASE_DIR)

class DriftDetector:
    """
    Monitors input data drift using statistical tests
    Compares production inputs against training data distribution
    """
    
    def __init__(self, training_data_path=None):
        if training_data_path is None:
            training_data_path = BASE_DIR / 'data/training_table_v2_CORRECTED.csv'
            
        # Check if file exists, if not try v1 as fallback
        if not os.path.exists(training_data_path):
             fallback = BASE_DIR / 'data/training_table_v1.csv'
             if os.path.exists(fallback):
                training_data_path = fallback
            
        try:
            self.training_data = pd.read_csv(training_data_path)
        except FileNotFoundError:
            # Fallback for testing/CI if no data
            print(f"Warning: Training data {training_data_path} not found. Drift detection disabled.")
            self.training_data = pd.DataFrame(columns=['rainfall_last_30d', 'monsoon_intensity', 'month_sin', 'month_cos'])
        
        self.stats_file = BASE_DIR / "app/monitoring/training_stats.json"
        self.drift_log = BASE_DIR / "app/monitoring/drift_alerts.log"
        
        # Create monitoring directory if not exists
        self.drift_log.parent.mkdir(exist_ok=True, parents=True)
        
        # Compute training statistics
        self._compute_training_stats()
    
    def _compute_training_stats(self):
        """Compute mean, std, min, max for each feature"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                self.training_stats = json.load(f)
            return
        
        features = ['rain_lag_7', 'rain_lag_30', 'rolling_30_rain', 
                   'temp', 'humidity', 'wind', 'pressure', 'month']
        
        stats_dict = {}
        for feature in features:
            stats_dict[feature] = {
                'mean': float(self.training_data[feature].mean()),
                'std': float(self.training_data[feature].std()),
                'min': float(self.training_data[feature].min()),
                'max': float(self.training_data[feature].max()),
                'q25': float(self.training_data[feature].quantile(0.25)),
                'q75': float(self.training_data[feature].quantile(0.75))
            }
        
        self.training_stats = stats_dict
        
        # Save for future use
        with open(self.stats_file, 'w') as f:
            json.dump(stats_dict, f, indent=2)
    
    def check_drift(self, features_dict):
        """
        Check if current features show drift from training distribution
        
        Returns:
            drift_detected: bool
            drift_report: dict with details
        """
        drift_alerts = []
        drift_scores = {}
        
        for feature, value in features_dict.items():
            if feature not in self.training_stats:
                continue
            
            stats = self.training_stats[feature]
            
            # Z-score check (how many std deviations away?)
            z_score = abs((value - stats['mean']) / stats['std']) if stats['std'] > 0 else 0
            drift_scores[feature] = z_score
            
            # Alert if > 3 standard deviations (99.7% rule)
            if z_score > 3:
                drift_alerts.append({
                    'feature': feature,
                    'value': value,
                    'expected_mean': stats['mean'],
                    'z_score': z_score,
                    'severity': 'HIGH'
                })
            
            # Warn if > 2 standard deviations
            elif z_score > 2:
                drift_alerts.append({
                    'feature': feature,
                    'value': value,
                    'expected_mean': stats['mean'],
                    'z_score': z_score,
                    'severity': 'MEDIUM'
                })
            
            # Check if outside min/max range (extreme outlier)
            if value < stats['min'] or value > stats['max']:
                drift_alerts.append({
                    'feature': feature,
                    'value': value,
                    'training_range': f"[{stats['min']}, {stats['max']}]",
                    'severity': 'CRITICAL',
                    'type': 'OUT_OF_RANGE'
                })
        
        drift_detected = len(drift_alerts) > 0
        
        drift_report = {
            'timestamp': datetime.now().isoformat(),
            'drift_detected': drift_detected,
            'num_alerts': len(drift_alerts),
            'alerts': drift_alerts,
            'z_scores': drift_scores
        }
        
        # Log drift if detected
        if drift_detected:
            self._log_drift(drift_report)
        
        return drift_detected, drift_report
    
    def _log_drift(self, report):
        """Log drift alerts to file"""
        with open(self.drift_log, 'a') as f:
            f.write(json.dumps(report) + '\n')
    
    def get_drift_summary(self, last_n_hours=24):
        """Get summary of drift alerts in last N hours"""
        if not self.drift_log.exists():
            return {"total_alerts": 0, "critical": 0, "high": 0, "medium": 0}
        
        cutoff_time = datetime.now().timestamp() - (last_n_hours * 3600)
        
        total = 0
        critical = 0
        high = 0
        medium = 0
        
        with open(self.drift_log, 'r') as f:
            for line in f:
                try:
                    report = json.loads(line)
                    report_time = datetime.fromisoformat(report['timestamp']).timestamp()
                    
                    if report_time >= cutoff_time:
                        total += 1
                        for alert in report['alerts']:
                            if alert['severity'] == 'CRITICAL':
                                critical += 1
                            elif alert['severity'] == 'HIGH':
                                high += 1
                            elif alert['severity'] == 'MEDIUM':
                                medium += 1
                except:
                    continue
        
        return {
            "total_alerts": total,
            "critical": critical,
            "high": high,
            "medium": medium,
            "last_n_hours": last_n_hours
        }

# Initialize global drift detector
drift_detector = None

def get_drift_detector():
    """Singleton pattern for drift detector"""
    global drift_detector
    if drift_detector is None:
        drift_detector = DriftDetector()
    return drift_detector
