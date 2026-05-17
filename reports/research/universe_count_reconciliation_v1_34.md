# Count Reconciliation - V1.34

```json
[
  {
    "step_name": "source_report_count",
    "total_count": 0,
    "count_2026": 12691,
    "delta_from_previous": 0,
    "delta_2026": 0,
    "explanation": "V1.32.4 documented count"
  },
  {
    "step_name": "raw_predictions",
    "total_count": 171648,
    "count_2026": 24360,
    "delta_from_previous": 171648,
    "delta_2026": 11669,
    "explanation": "Raw entries in prediction file"
  },
  {
    "step_name": "after_timestamp_alignment",
    "total_count": 5087,
    "count_2026": 0,
    "delta_from_previous": -166561,
    "delta_2026": -24360,
    "explanation": "Intersection of timestamps"
  },
  {
    "step_name": "rebuild_join",
    "total_count": 171648,
    "count_2026": 24360,
    "delta_from_previous": 166561,
    "delta_2026": 24360,
    "explanation": "Inner join result"
  },
  {
    "step_name": "after_warmup",
    "total_count": 171392,
    "count_2026": 24360,
    "delta_from_previous": -256,
    "delta_2026": 0,
    "explanation": "After min_periods warmup"
  },
  {
    "step_name": "after_filter_replay",
    "total_count": 74742,
    "count_2026": 8939,
    "delta_from_previous": -96650,
    "delta_2026": -15421,
    "explanation": "Selection count"
  }
]
```
