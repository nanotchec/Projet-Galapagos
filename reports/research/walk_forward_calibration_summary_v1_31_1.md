# Walk Forward Calibration Summary - v1.31.1

```json
{
  "raw_brier": 0.2889913457879318,
  "best_brier": 0.2409716462519486,
  "raw_ece": 0.15134236676612386,
  "best_ece": 0.02923227490249583,
  "best_method_by_ece": "platt_scaling",
  "best_method_by_brier": "bin_calibration",
  "best_method_selection_rule": "report multiple metric-specific winners; do not collapse to one universal best method",
  "calibration_improves_brier": true,
  "calibration_improves_ece": true,
  "calibration_stable_2026": true,
  "2026_raw_brier": 0.2809783092504697,
  "2026_calibrated_brier": 0.2373213743798436,
  "2026_raw_ece": 0.12782774989082904,
  "2026_calibrated_ece": 0.026923295902039637,
  "2026_brier_improved": true,
  "2026_ece_improved": true,
  "sample_count_2026": 24360,
  "final_verdict": "WALK_FORWARD_CALIBRATION_PROMISING_RESEARCH_ONLY",
  "recommended_next_step": "V1.32 EV-net filter research using calibrated probabilities",
  "no_preregistration_yet": true,
  "no_paper_live": true,
  "no_money_deployment": true,
  "ready_for_reviewer": false,
  "holdout_executed": false,
  "no_real_trading": true
}
```
