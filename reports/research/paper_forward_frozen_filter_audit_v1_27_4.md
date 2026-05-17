# Paper Forward Frozen Filter Audit V1 27 4

```json
{
  "filter_name": "low_frequency_strict_score",
  "policy": "horizon_only",
  "score_column": "predicted_probability",
  "selection_logic": "highest_score_per_period",
  "threshold": null,
  "temporal_frequency_rule": "7D",
  "max_trades_per_period": 1,
  "tie_break_explicit": false,
  "tie_break_warning": "Warning: Historical implementation has no explicit secondary sort key for equal scores.",
  "exact_filter_reconstructable": true,
  "forbidden_columns_detected": false,
  "missing_definition_fields": [],
  "status": "FROZEN_FILTER_AUDIT_PASSED_WITH_TIE_BREAK_WARNING"
}
```