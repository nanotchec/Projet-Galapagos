# Count Reconciliation - V1.34.1

```json
[
  {
    "step_name": "source_report_count",
    "universe_type": "source_report",
    "total_count": 0,
    "count_2026": 12691,
    "delta_from_previous": 0,
    "delta_2026": 0,
    "comparable_to_previous": false,
    "comparability_note": "",
    "explanation": "V1.32.4 documented count"
  },
  {
    "step_name": "raw_predictions",
    "universe_type": "raw_prediction_rows",
    "total_count": 171648,
    "count_2026": 24360,
    "delta_from_previous": 0,
    "delta_2026": 0,
    "comparable_to_previous": false,
    "comparability_note": "Universe change detected, delta not calculated.",
    "explanation": "Raw entries in prediction file"
  },
  {
    "step_name": "rebuild_join",
    "universe_type": "joined_prediction_rows",
    "total_count": 171648,
    "count_2026": 24360,
    "delta_from_previous": 0,
    "delta_2026": 0,
    "comparable_to_previous": true,
    "comparability_note": "",
    "explanation": "Inner join result"
  },
  {
    "step_name": "after_warmup",
    "universe_type": "ev_ready_rows",
    "total_count": 171392,
    "count_2026": 24360,
    "delta_from_previous": -256,
    "delta_2026": 0,
    "comparable_to_previous": true,
    "comparability_note": "",
    "explanation": "After min_periods warmup"
  },
  {
    "step_name": "after_filter_replay",
    "universe_type": "selected_rows",
    "total_count": 8939,
    "count_2026": 8939,
    "delta_from_previous": -162453,
    "delta_2026": -15421,
    "comparable_to_previous": true,
    "comparability_note": "",
    "explanation": "Selection count"
  }
]
```
