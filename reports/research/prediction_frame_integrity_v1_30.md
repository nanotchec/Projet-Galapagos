# Prediction Frame Integrity - Galapagos V1.30

## Status
- **PREDICTION_FRAME_INTEGRITY_PASSED**

## Details
```json
{
  "raw_rows": 171648,
  "unique_timestamps": 5087,
  "models_available": [
    "logistic_regression",
    "random_forest",
    "hist_gradient_boosting",
    "dummy_most_frequent"
  ],
  "targets_available": [
    "target_up_after_cost_6bar",
    "target_up_after_cost_12bar",
    "target_tp_before_sl_conservative"
  ],
  "selection_columns": [
    "timestamp",
    "model_name",
    "feature_set",
    "target",
    "split_name",
    "predicted_probability",
    "predicted_label",
    "macro_regime"
  ],
  "outcome_columns": [
    "timestamp",
    "actual_target",
    "forward_return_6bar",
    "forward_return_12bar",
    "cost_adjusted_forward_return"
  ],
  "forbidden_columns_in_selection": [],
  "integrity_status": "PREDICTION_FRAME_INTEGRITY_PASSED"
}
```
