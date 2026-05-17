# Preregistered Protocol Audit

```json
{
  "protocol_version": "v1.26.4",
  "protocol_created_from": "v1.26.3",
  "candidate_filter": "low_frequency_strict_score",
  "candidate_policy": "horizon_only",
  "protocol_locked": true,
  "filter_parameters_locked": true,
  "policy_parameters_locked": true,
  "selection_rules_locked": true,
  "metrics_locked": true,
  "data_sources_locked": true,
  "cost_model_locked": true,
  "baselines_locked": true,
  "no_hyperparameter_tuning": true,
  "no_reviewer_llm": true,
  "no_holdout": true,
  "no_real_trading": true,
  "success_criteria_complete": true,
  "main_metric": "mean_net_pnl_after_cost_pct",
  "locked_data_sources": {
    "predictions": "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet",
    "research_dataset": "data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet",
    "intrabar": "data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet",
    "trade_ledger_report": "reports/research/trade_ledger_intrabar_eval_v1_22_1.json"
  },
  "locked_filter_definition": {
    "filter_name": "low_frequency_strict_score",
    "policy": "horizon_only",
    "score_column": "predicted_probability",
    "selection_logic": "highest_score_per_period",
    "threshold": null,
    "threshold_type": "none",
    "rank_direction": "descending",
    "temporal_frequency_rule": "7D",
    "max_trades_per_period": 1,
    "period_flooring": "timestamp.dt.floor",
    "tie_break_rule": "pandas_current_order_after_score_sort",
    "tie_break_explicit": false,
    "tie_break_warning": "Warning: Historical implementation has no explicit secondary sort key for equal scores.",
    "required_input_columns": [
      "timestamp",
      "predicted_probability"
    ],
    "allowed_selection_columns": [
      "timestamp",
      "predicted_probability"
    ],
    "forbidden_selection_columns": [
      "forward_return_*",
      "gross_pnl_pct",
      "net_pnl_pct",
      "mfe_pct",
      "mae_pct",
      "exit_reason",
      "simulation_status"
    ],
    "causal_only": true,
    "uses_future_returns": false,
    "uses_realized_pnl": false,
    "uses_mfe_mae": false,
    "uses_exit_reason": false,
    "exact_filter_reconstructable": true
  },
  "forbidden_selection_columns": [
    "forward_return_*",
    "gross_pnl_pct",
    "net_pnl_pct",
    "mfe_pct",
    "mae_pct",
    "exit_reason",
    "simulation_status",
    "any realized future outcome"
  ],
  "input_reports_loaded": [
    "summary",
    "temporal",
    "sf_random",
    "cost",
    "placebo",
    "overfit",
    "stability"
  ],
  "input_report_consistency_status": "INPUT_REPORTS_CONSISTENT",
  "protocol_upgrade_reason": "source_audited_frozen_filter_definition",
  "frozen_filter_definition_complete": true,
  "frozen_filter_definition_status": "FILTER_DEFINITION_COMPLETE",
  "frozen_filter_definition_hash": "f5ba4007098b7a349a73b5d4d86eca51fa4348256987994dabf446bcdc9c1df2"
}
```
