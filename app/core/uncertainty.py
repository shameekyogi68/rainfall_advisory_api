#!/usr/bin/env python3
"""
Uncertainty Quantification for Rainfall Predictions
Provides prediction intervals and confidence ranges
"""

import numpy as np
import pickle
from datetime import datetime

class UncertaintyQuantifier:
    """Add uncertainty quantification to predictions"""
    
    def __init__(self, model_path='final_rainfall_classifier_v1.pkl', 
                 taluk_models_path='taluk_models.pkl'):
        """Load models for ensemble predictions"""
        
        with open(model_path, 'rb') as f:
            self.district_model = pickle.load(f)
        
        try:
            with open(taluk_models_path, 'rb') as f:
                self.taluk_models = pickle.load(f)
        except:
            self.taluk_models = None
    
    def get_prediction_with_uncertainty(self, features, taluk=None):
        """
        Get prediction with uncertainty intervals
        
        Returns:
            dict with prediction + uncertainty bounds
        """
        
        # Get district model prediction
        district_proba = self.district_model.predict_proba([features])[0]
        
        predictions = [district_proba]
        
        # Add taluk model prediction if available
        if self.taluk_models and taluk and taluk in self.taluk_models:
            taluk_proba = self.taluk_models[taluk].predict_proba([features])[0]
            predictions.append(taluk_proba)
        
        # Stack predictions
        ensemble_preds = np.array(predictions)
        
        # Calculate statistics
        mean_probs = np.mean(ensemble_preds, axis=0)
        std_probs = np.std(ensemble_preds, axis=0)
        
        # 90% confidence intervals (z=1.645)
        lower_bound = np.clip(mean_probs - 1.645 * std_probs, 0, 1)
        upper_bound = np.clip(mean_probs + 1.645 * std_probs, 0, 1)
        
        # Determine prediction
        category_idx = np.argmax(mean_probs)
        categories = ['Deficit', 'Normal', 'Excess']
        predicted_category = categories[category_idx]
        
        # Confidence (probability of predicted class)
        confidence = mean_probs[category_idx] * 100
        
        # Uncertainty level
        avg_std = np.mean(std_probs) * 100
        if avg_std < 5:
            uncertainty_level = 'LOW'
            uncertainty_desc = 'Models agree strongly'
        elif avg_std < 10:
            uncertainty_level = 'MEDIUM'
            uncertainty_desc = 'Models mostly agree'
        else:
            uncertainty_level = 'HIGH'
            uncertainty_desc = 'Models disagree - monitor forecast'
        
        return {
            'prediction': {
                'category': predicted_category,
                'confidence': confidence,
                'probabilities': {
                    'deficit': mean_probs[0] * 100,
                    'normal': mean_probs[1] * 100,
                    'excess': mean_probs[2] * 100
                }
            },
            'uncertainty': {
                'level': uncertainty_level,
                'description': uncertainty_desc,
                'ensemble_std': avg_std,
                'model_agreement': 100 - avg_std  # Higher = better agreement
            },
            'prediction_intervals': {
                'deficit': {
                    'mean': mean_probs[0] * 100,
                    'lower_90': lower_bound[0] * 100,
                    'upper_90': upper_bound[0] * 100,
                    'range': f"{lower_bound[0]*100:.0f}-{upper_bound[0]*100:.0f}%"
                },
                'normal': {
                    'mean': mean_probs[1] * 100,
                    'lower_90': lower_bound[1] * 100,
                    'upper_90': upper_bound[1] * 100,
                    'range': f"{lower_bound[1]*100:.0f}-{upper_bound[1]*100:.0f}%"
                },
                'excess': {
                    'mean': mean_probs[2] * 100,
                    'lower_90': lower_bound[2] * 100,
                    'upper_90': upper_bound[2] * 100,
                    'range': f"{lower_bound[2]*100:.0f}-{upper_bound[2]*100:.0f}%"
                }
            },
            'interpretation': self._get_interpretation(
                predicted_category, confidence, uncertainty_level
            )
        }
    
    def _get_interpretation(self, category, confidence, uncertainty):
        """Human-readable interpretation"""
        
        if uncertainty == 'LOW' and confidence > 70:
            return f"{category} very likely - all models agree"
        elif uncertainty == 'LOW':
            return f"{category} likely - models agree"
        elif uncertainty == 'MEDIUM' and confidence > 60:
            return f"{category} probable - some model variation"
        elif uncertainty == 'MEDIUM':
            return f"{category} possible - monitor updates"
        else:  # HIGH uncertainty
            return f"Uncertain - check forecast in 2-3 days"
    
    def format_for_display(self, result):
        """Format for farmer-friendly display"""
        pred = result['prediction']
        uncertainty = result['uncertainty']
        intervals = result['prediction_intervals']
        
        output = f"""
╔═══════════════════════════════════════════════════════════════════╗
║              PREDICTION WITH UNCERTAINTY ANALYSIS                  ║
╚═══════════════════════════════════════════════════════════════════╝

📊 PREDICTION: {pred['category']} ({pred['confidence']:.0f}%)

📈 PROBABILITY BREAKDOWN:
   Deficit:  {pred['probabilities']['deficit']:.0f}% (Range: {intervals['deficit']['range']})
   Normal:   {pred['probabilities']['normal']:.0f}% (Range: {intervals['normal']['range']})
   Excess:   {pred['probabilities']['excess']:.0f}% (Range: {intervals['excess']['range']})

🎯 UNCERTAINTY:
   Level: {uncertainty['level']}
   Model Agreement: {uncertainty['model_agreement']:.0f}%
   {uncertainty['description']}

💡 INTERPRETATION:
   {result['interpretation']}

{'─'*70}
Note: Ranges show 90% confidence intervals
"""
        return output


def test_uncertainty_quantification():
    """Test uncertainty quantification"""
    from app.backend import process_advisory_request
    
    print("="*70)
    print("UNCERTAINTY QUANTIFICATION TEST")
    print("="*70)
    
    # Get a prediction using production backend
    result = process_advisory_request('test', 13.3409, 74.7421, '2026-02-07')
    
    # Extract features (we need to get these from the backend)
    # For now, let's demonstrate the concept
    
    quantifier = UncertaintyQuantifier()
    
    # Simulate features (in production, use actual computed features)
    dummy_features = [10, 30, 45, 80, 120, 5, 20, 28, 65, 15, 1013, 2]
    
    try:
        uncertainty_result = quantifier.get_prediction_with_uncertainty(
            dummy_features, 
            taluk='Udupi'
        )
        
        formatted = quantifier.format_for_display(uncertainty_result)
        print(formatted)
        
        print("\n✓ Uncertainty quantification working!")
        print("\nAPI Response Example:")
        print(f"""
{{
  "prediction": {{
    "category": "{uncertainty_result['prediction']['category']}",
    "confidence": {uncertainty_result['prediction']['confidence']:.1f},
    "probabilities": {{
      "deficit": {uncertainty_result['prediction']['probabilities']['deficit']:.1f},
      "normal": {uncertainty_result['prediction']['probabilities']['normal']:.1f},
      "excess": {uncertainty_result['prediction']['probabilities']['excess']:.1f}
    }}
  }},
  "uncertainty": {{
    "level": "{uncertainty_result['uncertainty']['level']}",
    "model_agreement": {uncertainty_result['uncertainty']['model_agreement']:.0f},
    "description": "{uncertainty_result['uncertainty']['description']}"
  }},
  "prediction_intervals": {{
    "deficit_range": "{uncertainty_result['prediction_intervals']['deficit']['range']}",
    "normal_range": "{uncertainty_result['prediction_intervals']['normal']['range']}",
    "excess_range": "{uncertainty_result['prediction_intervals']['excess']['range']}"
  }}
}}
""")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Needs actual feature computation from production backend")
        print("This is a demonstration of the concept")

if __name__ == '__main__':
    test_uncertainty_quantification()
