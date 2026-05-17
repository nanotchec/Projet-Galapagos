# Canonical Universe Selection Frame Audit - V1.36.3

```json
{
  "selection_frame_rows": 171648,
  "selection_frame_rows_2026": 24360,
  "selection_frame_columns": [
    "timestamp",
    "model_name",
    "feature_set",
    "target",
    "split_name",
    "predicted_probability",
    "predicted_label",
    "ev_proxy_ready",
    "warmup_ready"
  ],
  "allowed_selection_columns": [
    "timestamp",
    "model_name",
    "feature_set",
    "target",
    "split_name",
    "predicted_probability",
    "predicted_label",
    "calibrated_probability",
    "avg_win_past",
    "avg_loss_past",
    "cost_proxy",
    "ev_calibrated_proxy",
    "ev_proxy_ready",
    "warmup_ready"
  ],
  "forbidden_selection_columns": [
    "actual_target",
    "forward_return_1h",
    "forward_return_4h",
    "forward_return_1d",
    "cost_adjusted_forward_return",
    "future_return",
    "pnl",
    "realized_pnl",
    "exit_reason",
    "mae_realized",
    "mfe_realized",
    "outcome"
  ],
  "forbidden_columns_found": [],
  "raw_outcome_columns_detected": [],
  "outcome_columns_excluded_from_selection": true,
  "causal_columns_count": 9,
  "selection_frame_status": "SELECTION_FRAME_CAUSAL_CLEAN"
}
```
