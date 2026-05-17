# Point In Time Feature Audit - Galapagos V1.30

## Status
- **POINT_IN_TIME_AUDIT_FAILED_FORBIDDEN_SELECTION_COLUMNS**

## Details
```json
{
  "total_columns": 12,
  "allowed_feature_columns": [
    "predicted_probability",
    "predicted_label",
    "macro_regime"
  ],
  "metadata_columns": [
    "timestamp",
    "model_name",
    "feature_set",
    "target",
    "split_name"
  ],
  "forbidden_outcome_columns": [
    "actual_target",
    "forward_return_6bar",
    "forward_return_12bar",
    "cost_adjusted_forward_return"
  ],
  "unknown_columns": [],
  "unknown_requires_manual_review": false,
  "point_in_time_status": "POINT_IN_TIME_AUDIT_FAILED_FORBIDDEN_SELECTION_COLUMNS"
}
```
