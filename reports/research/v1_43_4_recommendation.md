# V1 43 Recommendation V1.43.4

Status: COMPLETE

### Summary
```json
{
  "version": "V1.43.4",
  "recommended_next_step": "research regime-aware raw/alpha feature set with stability constraints, keeping model outputs and EV proxies diagnostic-only",
  "evidence_classification": "DIAGNOSTIC_ONLY",
  "recommended_raw_feature_families_for_v1_44": [
    "microstructure",
    "price_return",
    "regime_proxy",
    "trend_momentum",
    "volatility",
    "volume_liquidity"
  ],
  "recommended_alpha_feature_families_for_v1_44": [
    "alpha_score_family"
  ],
  "diagnostic_only_model_output_features": [
    "predicted_probability",
    "calibrated_probability_rebuilt",
    "calibrated_probability",
    "predicted_probability_calibrated"
  ],
  "diagnostic_only_ev_proxy_features": [
    "avg_win_past_rebuilt",
    "avg_loss_past_rebuilt",
    "avg_win_past",
    "avg_loss_past",
    "cost_proxy_rebuilt",
    "cost_proxy",
    "ev_calibrated_proxy_rebuilt",
    "ev_calibrated_proxy",
    "ev_raw_proxy",
    "ev_proxy_ready",
    "payoff_estimate_ready",
    "basis_proxy",
    "premium_proxy"
  ],
  "alpha_score_or_model_output_removed": true,
  "no_new_filter": true,
  "no_strategy_validated": true,
  "no_preregistration_yet": true,
  "no_paper_live": true,
  "no_money_deployment": true,
  "no_real_trading": true,
  "holdout_executed": false,
  "codex_cli_called": false
}
```