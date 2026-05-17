# Loss Decomposition - V1.33.1

```json
{
  "drivers": {
    "calibration_driver": "CALIBRATION_STABLE_BUT_PAYOFF_DEGRADED",
    "ev_proxy_driver": "EV_PROXY_OVERESTIMATES_2026",
    "payoff_driver": "PAYOFF_ASYMMETRY_DEGRADED_2026",
    "cost_driver": "EDGE_NEGATIVE_BEFORE_COSTS",
    "regime_driver": "REGIME_NOT_EXPLANATORY",
    "score_shift_driver": "SCORE_DISTRIBUTION_STABLE_OUTCOME_DEGRADED",
    "feature_shift_driver": "FEATURE_DISTRIBUTION_STABLE",
    "concentration_driver": "LOSSES_DIFFUSE"
  },
  "primary_driver": "EV_PROXY_DEGRADATION",
  "secondary_drivers": [
    "calibration_driver",
    "payoff_driver",
    "score_shift_driver"
  ],
  "status": "REVERSAL_DRIVER_IDENTIFIED"
}
```
