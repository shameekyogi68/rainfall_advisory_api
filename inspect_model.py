
import pickle
import sys
import os

model_path = 'models/final_rainfall_classifier_v1.pkl'

try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f"Model Type: {type(model)}")
    print(f"Model Parameters: {model.get_params()}")
    
    if hasattr(model, 'estimators_'):
        print(f"Number of Estimators: {len(model.estimators_)}")
        
except Exception as e:
    print(f"Error loading model: {e}")
