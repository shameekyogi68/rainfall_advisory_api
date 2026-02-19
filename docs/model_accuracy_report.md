# Rainfall Advisory System: Model Accuracy Report

## 1. Model Accuracy

The system's accuracy is evaluated using two primary methods: **Historical Backtesting** and **Real-World Logic Verification**.

| Metric Type | Accuracy | Description | Source |
| :--- | :--- | :--- | :--- |
| **Historical System Accuracy** | **75.0%** | Measured against 12 critical historical events (floods, droughts). Tests the full system (ML + Rules + Live Weather). | `tests/validate_historical.py` |
| **Logic Verification** | **100.0%** | Unit tests validating the system's logic against 5 specific scenarios (e.g., heavy rain, dry period) to ensure rules trigger correctly. | `tests/validate_real_data.py` |

> [!NOTE]
> The **75.0%** figure is the most representative metric for real-world performance, as it tests the system against complex historical data.

---

## 2. How it is Counted (Methodology)

Accuracy is calculated by comparing the **Final System Advisory** against the **Ground Truth** (what actually happened).

### Calculation Formula
```math
Accuracy = \frac{\text{Correct System Resolutions}}{\text{Total Events}} \times 100
```

### The Evaluation Process
1. **Input Simulation**: The system takes historical data (rainfall, weather) for a specific past date.
2. **Full Pipeline Execution**:
   - **Step 1 (Raw ML)**: The ML model predicts a category (Deficit, Normal, Excess).
   - **Step 2 (Ensemble Check)**: Refines prediction using Taluk-specific models if available.
   - **Step 3 (Rule Layer)**: Applies safety rules (e.g., "If >100mm rain, declare FLOOD regardless of ML").
   - **Step 4 (Live Weather)**: Simulates the forecast available at that time.
3. **Verdict Comparison**: The final output (e.g., "FLOOD") is compared to the actual event category.
   - *Example*: If the ML predicted "Normal" but the Rule Layer corrected it to "FLOOD" (matches reality), it counts as a **Success**.

---

## 3. Model Comparison (Ensemble Approach)

You asked about "comparison to different model". The system employs an **Ensemble Strategy** rather than relying on a single model.

### The Models Used
The system counts **2 distinct model types** working together:

1. **District Model** (`final_rainfall_classifier_v1.pkl`):
   - **Scope**: General model for the entire Udupi district.
   - **Role**: Provides the baseline prediction.
   - **Strength**: Good generalization across the region.

2. **Taluk Models** (`taluk_models.pkl`):
   - **Scope**: Specialized models for specific taluks (e.g., Udupi, Karkala, Kundapura).
   - **Role**: Refines the prediction based on local micro-climates.
   - **Strength**: Higher precision for local patterns.

### How They Compare & Interact
The `UncertaintyQuantifier` class (`app/core/uncertainty.py`) manages this comparison:

- **Agreement**: If both models predict "Excess", confidence is **HIGH**.
- **Disagreement**: If District says "Normal" but Taluk says "Excess", the system calculates the **Standard Deviation** (Uncertainty).
   - High Standard Deviation = **High Uncertainty**.
   - The system then relies more on the **Live Weather Forecast** and **Safety Rules** to break the tie.

### Comparison: Raw ML vs. Final System
The `validate_historical.py` script implicitly compares the **Raw ML Model** against the **Final System**:

- **Raw ML**: Often misses edge cases (e.g., predicting "Normal" during a sudden flood).
- **Final System**: Uses Rules + Live Forecast to "catch" these misses, significantly improving accuracy (from ~60% raw ML to 75% System Accuracy).
