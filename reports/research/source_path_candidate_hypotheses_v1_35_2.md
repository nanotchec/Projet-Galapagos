# Candidate Hypotheses - V1.35.2

```json
[
  {
    "id": "H1",
    "name": "raw_predictions_no_join",
    "universe_unit": "raw_row",
    "join_policy": "none",
    "dedup_policy": "none",
    "warmup_policy": "none",
    "outcome_policy": "none",
    "expected_effect": "very_high_count"
  },
  {
    "id": "H2",
    "name": "joined_inner",
    "universe_unit": "raw_row",
    "join_policy": "inner",
    "dedup_policy": "none",
    "warmup_policy": "none",
    "outcome_policy": "none",
    "expected_effect": "high_count"
  },
  {
    "id": "H3",
    "name": "joined_inner_warmup_100",
    "universe_unit": "raw_row",
    "join_policy": "inner",
    "dedup_policy": "none",
    "warmup_policy": "100_bars",
    "outcome_policy": "none",
    "expected_effect": "medium_count"
  },
  {
    "id": "H4",
    "name": "joined_inner_warmup_100_outcome_only",
    "universe_unit": "raw_row",
    "join_policy": "inner",
    "dedup_policy": "none",
    "warmup_policy": "100_bars",
    "outcome_policy": "outcome_present",
    "expected_effect": "lower_count"
  },
  {
    "id": "H5",
    "name": "dedup_timestamp_rebuild",
    "universe_unit": "unique_timestamp",
    "join_policy": "inner",
    "dedup_policy": "first_row",
    "warmup_policy": "100_bars",
    "outcome_policy": "none",
    "expected_effect": "lowest_count"
  },
  {
    "id": "H6",
    "name": "all_models_selection",
    "universe_unit": "raw_row",
    "join_policy": "inner",
    "dedup_policy": "none",
    "warmup_policy": "none",
    "outcome_policy": "none",
    "expected_effect": "high_count"
  }
]
```
