# Canonical Universe Definition - V1.37

```json
{
  "universe_name": "canonical_ev_strict_trade_universe",
  "universe_version": "V1.37",
  "count_semantics_version": "v1.37_explicit_split",
  "raw_prediction_universe_definition": "all available prediction signals from source ML models",
  "canonical_opportunity_universe_definition": "full research universe after canonical join, dedup, and warmup, with formal selection/outcome split",
  "ev_filter_reference_status": "EV_FILTER_REFERENCE_IMPORTED_FROM_V1_35_3",
  "base_data": {
    "predictions_path": "<USER_ROOT>/.gemini/antigravity/brain/f29d1dba-c6f6-4aa8-abaa-164d9516cd0a/scratch/mock_preds.parquet",
    "dataset_path": "<USER_ROOT>/.gemini/antigravity/brain/f29d1dba-c6f6-4aa8-abaa-164d9516cd0a/scratch/mock_dataset.parquet",
    "intrabar_path": "<PROJECT_ROOT>/tests/mock_intrabar_gap.parquet"
  },
  "symbol": "BTC",
  "timeframe": "4h",
  "canonical_key_policy": {
    "canonical_key_columns": [
      "timestamp",
      "model_name",
      "feature_set",
      "target",
      "split_name"
    ],
    "key_null_policy": "STRICT_NO_NULLS",
    "duplicate_exact_key_policy": "KEEP_FIRST"
  },
  "dataset_split_policy": {
    "version": "V1.37",
    "index_columns": [
      "timestamp",
      "model_name",
      "feature_set",
      "target",
      "split_name"
    ],
    "selection_columns": [
      "timestamp",
      "model_name",
      "feature_set",
      "target",
      "split_name",
      "predicted_probability",
      "predicted_label",
      "calibrated_probability",
      "avg_win_past",
      "avg_loss_past",
      "cost_proxy",
      "ev_calibrated_proxy",
      "ev_proxy_ready",
      "warmup_ready"
    ],
    "outcome_columns": [
      "timestamp",
      "actual_target",
      "forward_return_4h",
      "pnl",
      "exit_reason",
      "realized_pnl"
    ],
    "forbidden_selection_columns": [
      "actual_target",
      "forward_return_1h",
      "forward_return_4h",
      "forward_return_1d",
      "cost_adjusted_forward_return",
      "future_return",
      "pnl",
      "realized_pnl",
      "exit_reason",
      "mae_realized",
      "mfe_realized",
      "outcome"
    ],
    "split_policy_status": "CANONICAL_DATASET_SPLIT_POLICY_DEFINED"
  },
  "warning_resolution_status": "CANONICAL_INPUT_OUTCOME_WARNING_RESOLVED",
  "calibration_policy": "walk_forward_calibration_v1_31",
  "ev_proxy_policy": "NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
  "cost_policy": "NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
  "leakage_policy": "CANONICAL_UNIVERSE_FORMAL_SPLIT_NO_SELECTION_LEAKAGE",
  "reproducibility_policy": "FINGERPRINT_STRICT",
  "no_strategy_validated": true,
  "no_filter_applied_to_canonical_opportunity_universe": true
}
```
