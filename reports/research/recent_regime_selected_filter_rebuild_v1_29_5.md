# Recent Regime Selected Filter Rebuild V1 29 5

```json
{
  "raw_prediction_rows": 171648,
  "dedup_policy_used": "first_stable_per_timestamp",
  "model_filtering_applied": true,
  "excluded_models": [
    "dummy_most_frequent"
  ],
  "deduped_rows": 5087,
  "selected_count_final": 225,
  "expected_v1_29_3_selected_count": 225,
  "selected_count_matches_v1_29_3": true,
  "forbidden_columns_found": [
    "forward_return_6bar",
    "forward_return_12bar"
  ],
  "selection_columns": [
    "timestamp",
    "model_name",
    "feature_set",
    "target",
    "split_name",
    "predicted_probability",
    "predicted_label",
    "actual_target",
    "forward_return_6bar",
    "forward_return_12bar",
    "cost_adjusted_forward_return"
  ],
  "outcome_column_used": "forward_return_12bar",
  "rebuild_status": "REBUILD_COMPLETE"
}
```
