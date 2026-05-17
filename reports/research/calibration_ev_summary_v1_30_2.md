# Calibration Ev Summary - Galapagos v1.30.2

## Status
- **POINT_IN_TIME_AUDIT_PASSED_WITH_CLASSIFIED_OUTCOMES**

## Details
```json
{
  "point_in_time_status": "POINT_IN_TIME_AUDIT_PASSED_WITH_CLASSIFIED_OUTCOMES",
  "raw_dataset_contains_outcomes": true,
  "raw_dataset_outcomes_classified": true,
  "prediction_frame_integrity_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
  "selection_leakage_status": "CLEAN",
  "calibration_global_status": "CALIBRATION_DEGRADED",
  "calibration_temporal_status": "CALIBRATION_STABLE",
  "calibration_regime_status": "REGIME_CALIBRATION_AVAILABLE",
  "payoff_asymmetry_status": "PAYOFF_ASYMMETRY_UNFAVORABLE",
  "cost_model_status": "COST_MODEL_FOUNDATION_READY_FOR_EV_PROXY",
  "costs_isolated_from_gross": true,
  "ev_proxy_status": "EV_PROXY_RESEARCH_FOUNDATION_READY",
  "probability_threshold_status": "NOT_VALIDATED",
  "final_verdict": "RAW_PROBABILITY_THRESHOLD_NOT_READY",
  "recommended_next_steps": [
    "V1.31 calibrate probabilities on walk-forward validation only",
    "V1.31 build causal regime matrix",
    "V1.31 improve cost model",
    "V1.31 build EV-net candidate filters"
  ],
  "no_preregistration_yet": true,
  "no_paper_live": true,
  "no_money_deployment": true,
  "ready_for_reviewer": false,
  "holdout_executed": false,
  "no_real_trading": true
}
```
