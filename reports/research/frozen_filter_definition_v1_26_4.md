# Frozen Filter Source Audit

```json
{
  "version": "v1.26.4",
  "filter_definition": {
    "filter_name": "low_frequency_strict_score",
    "policy": "horizon_only",
    "score_column": "predicted_probability",
    "selection_logic": "highest_score_per_period",
    "threshold": null,
    "threshold_type": "none",
    "rank_direction": "descending",
    "temporal_frequency_rule": "7D",
    "max_trades_per_period": 1,
    "period_flooring": "timestamp.dt.floor",
    "tie_break_rule": "pandas_current_order_after_score_sort",
    "tie_break_explicit": false,
    "tie_break_warning": "Warning: Historical implementation has no explicit secondary sort key for equal scores.",
    "required_input_columns": [
      "timestamp",
      "predicted_probability"
    ],
    "allowed_selection_columns": [
      "timestamp",
      "predicted_probability"
    ],
    "forbidden_selection_columns": [
      "forward_return_*",
      "gross_pnl_pct",
      "net_pnl_pct",
      "mfe_pct",
      "mae_pct",
      "exit_reason",
      "simulation_status"
    ],
    "causal_only": true,
    "uses_future_returns": false,
    "uses_realized_pnl": false,
    "uses_mfe_mae": false,
    "uses_exit_reason": false,
    "exact_filter_reconstructable": true
  },
  "source_extraction_status": "SOURCE_MATCHED_CODE_AND_REPORTS",
  "source_match_details": "Found rule with period 7D and score column predicted_probability",
  "definition_hash": "f5ba4007098b7a349a73b5d4d86eca51fa4348256987994dabf446bcdc9c1df2",
  "exact_filter_reconstructable": true
}
```
