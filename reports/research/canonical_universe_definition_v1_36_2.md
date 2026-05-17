# Canonical Universe Definition - V1.36.2

```json
{
  "universe_name": "canonical_ev_strict_trade_universe",
  "universe_version": "V1.36.2",
  "count_semantics_version": "v1.36.2_explicit",
  "raw_prediction_universe_definition": "all available prediction signals from source ML models",
  "canonical_opportunity_universe_definition": "full research universe after canonical join, dedup, and warmup, without trading filter",
  "ev_filter_reference_universe_definition": "historical diagnostic reference trades using filter_ev_gt_cost_buffer logic (not equivalent to raw probability thresholds)",
  "ev_filter_reference_status": "EV_FILTER_REFERENCE_IMPORTED_FROM_V1_35_3",
  "base_data": {
    "predictions_path": "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet",
    "dataset_path": "data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet",
    "intrabar_path": "data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet"
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
  "dataset_join_policy": {
    "join_keys": [
      "timestamp"
    ],
    "join_type": "inner",
    "purpose": "align signals with feature dataset"
  },
  "outcome_alignment_policy": {
    "outcome_join_keys": [
      "timestamp",
      "model_name",
      "feature_set",
      "target"
    ],
    "join_type": "inner",
    "purpose": "align signals with future outcomes"
  },
  "calibration_policy": "walk_forward_calibration_v1_31",
  "ev_proxy_policy": "ev_calibrated_proxy = (calibrated_probability * avg_win_past) - ((1 - calibrated_probability) * avg_loss_past) - cost_proxy",
  "cost_policy": "cost_proxy_v1_32 (causal estimate)",
  "warmup_policy": "WARMUP_POLICY_EXPLICIT_NON_DROPPING",
  "outcome_policy": "OUTCOME_FRAME_SEPARATED",
  "allowed_selection_columns": [
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
  "allowed_outcome_columns": [
    "feature_set",
    "target",
    "timestamp",
    "model_name",
    "actual_target"
  ],
  "leakage_policy": "CANONICAL_UNIVERSE_NO_SELECTION_LEAKAGE",
  "reproducibility_policy": "FINGERPRINT_STRICT",
  "no_strategy_validated": true,
  "no_filter_applied_to_canonical_opportunity_universe": true
}
```
