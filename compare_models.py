
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# Load Data
data_path = 'data/training_table_v2_CORRECTED.csv'
df = pd.read_csv(data_path)

# Features & Target
features = [
    'rain_lag_7', 'rain_lag_30', 'rolling_30_rain', 'rolling_60_rain', 
    'rolling_90_rain', 'dry_days_count', 'rain_deficit', 
    'temp', 'humidity', 'wind', 'pressure', 'month'
]
target = 'target_category'

X = df[features]
y = df[target]

# Handle basic cleaning (fill NaNs if any)
X = X.fillna(0)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features (important for Logistic Regression & KNN)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Define Models
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Decision Tree": DecisionTreeClassifier(random_state=42),
    "Random Forest (Current)": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    "Gradient Boosting (XGB-like)": GradientBoostingClassifier(random_state=42),
    "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=5)
}

print(f"{'Algorithm':<30} | {'Accuracy':<10}")
print("-" * 45)

results = []

for name, model in models.items():
    # Use scaled data for LR and KNN, raw for Trees (typically fine, but let's use scaled for consistency or raw where appropriate)
    # Tree models don't need scaling, but it doesn't hurt. LR/KNN DO need it.
    # To be fair, let's use scaled for all or handled inside.
    
    if name in ["Logistic Regression", "K-Nearest Neighbors"]:
        clf = model.fit(X_train_scaled, y_train)
        preds = clf.predict(X_test_scaled)
    else:
        clf = model.fit(X_train, y_train)
        preds = clf.predict(X_test)
        
    acc = accuracy_score(y_test, preds)
    results.append((name, acc))
    print(f"{name:<30} | {acc:.4f}")

# Find best
best_model = max(results, key=lambda x: x[1])
print("-" * 45)
print(f"Best Performing: {best_model[0]} ({best_model[1]:.4f})")
print(f"Current System (Random Forest): {results[2][1]:.4f}")
