# Ev Filter Causal Safety Audit - v1.32.3

```json
{
  "causal_safety_status": "EV_FILTER_CAUSAL_SAFETY_PASSED_WITH_EXCLUSIONS",
  "verified_logic": [
    "payoff_estimator_uses_past_only",
    "calibration_uses_walk_forward_past",
    "selection_excludes_future_outcome_columns"
  ],
  "passed_filters": [
    "filter_ev_gt_0",
    "filter_ev_gt_cost_buffer",
    "filter_prob_65_ev_pos",
    "filter_ev_top_quantile_causal"
  ],
  "excluded_filters": [
    "filter_ev_top_quantile_non_causal"
  ],
  "violations": [
    "Non-causal filter detected: filter_ev_top_quantile_non_causal"
  ],
  "default_payoff_detected": false,
  "full_period_quantile_detected": true
}
```
