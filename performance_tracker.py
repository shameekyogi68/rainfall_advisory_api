import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class PerformanceTracker:
    """
    Track ML model performance in production
    Log predictions and (when available) ground truth
    Calculate accuracy metrics
    """
    
    def __init__(self):
        self.predictions_db = Path("monitoring/predictions_db.jsonl")
        self.metrics_file = Path("monitoring/performance_metrics.json")
        
        Path("monitoring").mkdir(exist_ok=True)
    
    def log_prediction(self, user_id, taluk, features, prediction, confidence, alert_sent):
        """
        Log a prediction for future performance analysis
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'taluk': taluk,
            'features': features,
            'prediction': prediction,
            'confidence': confidence,
            'alert_sent': alert_sent,
            'ground_truth': None  # Will be updated later if available
        }
        
        with open(self.predictions_db, 'a') as f:
            f.write(json.dumps(record) + '\n')
    
    def update_ground_truth(self, user_id, timestamp, actual_category):
        """
        Update prediction with actual observed outcome
        (Called when we get real rainfall data for that month)
        """
        # This would be called by a monthly batch job
        # For now, just log the update
        update = {
            'timestamp': datetime.now().isoformat(),
            'prediction_timestamp': timestamp,
            'user_id': user_id,
            'actual_category': actual_category
        }
        
        update_file = Path("monitoring/ground_truth_updates.jsonl")
        with open(update_file, 'a') as f:
            f.write(json.dumps(update) + '\n')
    
    def calculate_metrics(self, last_n_days=30):
        """
        Calculate performance metrics from logged predictions
        (Only for predictions where ground truth is available)
        """
        if not self.predictions_db.exists():
            return {
                "status": "no_data",
                "message": "No predictions logged yet"
            }
        
        # Load predictions
        predictions = []
        with open(self.predictions_db, 'r') as f:
            for line in f:
                try:
                    predictions.append(json.loads(line))
                except:
                    continue
        
        if not predictions:
            return {"status": "no_data"}
        
        # Calculate basic stats
        total_predictions = len(predictions)
        
        # Count by category
        category_counts = defaultdict(int)
        for pred in predictions:
            category_counts[pred['prediction']] += 1
        
        # Count alerts sent
        alerts_sent = sum(1 for p in predictions if p['alert_sent'])
        
        # Average confidence scores
        avg_confidences = {}
        for category in ['Deficit', 'Normal', 'Excess']:
            cat_preds = [p for p in predictions if p['prediction'] == category]
            if cat_preds:
                avg_conf = sum(p['confidence'].get(category, 0) for p in cat_preds) / len(cat_preds)
                avg_confidences[category] = avg_conf
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'period_days': last_n_days,
            'total_predictions': total_predictions,
            'category_distribution': dict(category_counts),
            'alerts_sent': alerts_sent,
            'alert_rate': alerts_sent / total_predictions if total_predictions > 0 else 0,
            'avg_confidence_scores': avg_confidences
        }
        
        # Save metrics
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        return metrics
    
    def get_latest_metrics(self):
        """Get most recently computed metrics"""
        if not self.metrics_file.exists():
            return self.calculate_metrics()
        
        with open(self.metrics_file, 'r') as f:
            return json.load(f)
    
    def get_prediction_stats_by_taluk(self):
        """Get prediction breakdown by taluk"""
        if not self.predictions_db.exists():
            return {}
        
        taluk_stats = defaultdict(lambda: {'count': 0, 'categories': defaultdict(int)})
        
        with open(self.predictions_db, 'r') as f:
            for line in f:
                try:
                    pred = json.loads(line)
                    taluk = pred['taluk']
                    taluk_stats[taluk]['count'] += 1
                    taluk_stats[taluk]['categories'][pred['prediction']] += 1
                except:
                    continue
        
        return dict(taluk_stats)

# Global tracker instance
performance_tracker = None

def get_performance_tracker():
    """Singleton pattern"""
    global performance_tracker
    if performance_tracker is None:
        performance_tracker = PerformanceTracker()
    return performance_tracker
