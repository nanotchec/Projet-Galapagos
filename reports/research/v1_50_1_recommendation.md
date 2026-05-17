# Recommendation V1.50.1

```json
{
  "version": "V1.50.1",
  "previous_base": "V1.50",
  "micro_regime_diagnostic_base_version": "V1.49.1",
  "microstructure_regime_label_base_version": "V1.48.1",
  "microstructure_feature_base_version": "V1.47",
  "canonical_base_version": "V1.37.2",
  "input_guard_status": "MICROSTRUCTURE_COVERAGE_INPUT_GUARD_PASSED",
  "intrabar_coverage_status": "MICROSTRUCTURE_INTRABAR_COVERAGE_AUDIT_COMPLETED",
  "timestamp_alignment_status": "MICROSTRUCTURE_TIMESTAMP_ALIGNMENT_AUDIT_COMPLETED",
  "missingness_profile_status": "MICROSTRUCTURE_MISSINGNESS_PROFILE_COMPLETED",
  "gap_detection_status": "MICROSTRUCTURE_GAP_DETECTION_COMPLETED",
  "session_quality_status": "MICROSTRUCTURE_SESSION_QUALITY_PROFILE_COMPLETED",
  "feature_availability_status": "MICROSTRUCTURE_FEATURE_AVAILABILITY_COMPLETED",
  "label_coverage_impact_status": "MICROSTRUCTURE_LABEL_COVERAGE_IMPACT_COMPLETED",
  "coverage_vs_failure_status": "MICROSTRUCTURE_COVERAGE_VS_FAILURE_COMPLETED",
  "quality_policy_status": "MICROSTRUCTURE_QUALITY_POLICY_COMPLETED",
  "coverage_scorecard_status": "MICROSTRUCTURE_COVERAGE_SCORECARD_COMPLETED",
  "recommendation_status": "MICROSTRUCTURE_COVERAGE_RECOMMENDATION_COMPLETED",
  "assessed_microstructure_features": [
    "amihud_illiquidity",
    "realized_vol_proxy",
    "volume_vol_ratio",
    "intraday_range"
  ],
  "quality_pass_features": [],
  "quality_weak_features": [],
  "quality_blocked_features": [
    "amihud_illiquidity",
    "realized_vol_proxy",
    "volume_vol_ratio",
    "intraday_range"
  ],
  "coverage_problem_periods": [
    "2024",
    "2025",
    "2026"
  ],
  "coverage_problem_2026": true,
  "coverage_impacts_label_quality": true,
  "recommended_data_actions": [
    "Improve intrabar coverage for 2026"
  ],
  "recommended_keep_for_next_research": [
    "amihud_illiquidity",
    "realized_vol_proxy"
  ],
  "recommended_rework": [
    "volume_vol_ratio"
  ],
  "final_verdict": "MICROSTRUCTURE_COVERAGE_INCONCLUSIVE",
  "recommended_next_step": "improve microstructure data coverage before further regime diagnostics",
  "evidence_classification": "RESEARCH_ONLY",
  "no_new_filter": true,
  "no_strategy_validated": true,
  "no_preregistration_yet": true,
  "no_paper_live": true,
  "no_real_trading": true,
  "holdout_executed": false,
  "codex_cli_called": false,
  "real_orders_possible": false
}
```
