# Regime Feature Stability Scorecard V1.43.2

Status: COMPLETE

### Summary
```json
{
  "feature_stability_scorecard_status": "FEATURE_STABILITY_SCORECARD_COMPLETE",
  "family_summary": {
    "alpha_score_or_model_output": {
      "STABLE_CANDIDATE": 26
    },
    "microstructure": {
      "STABLE_CANDIDATE": 3
    },
    "price_return": {
      "STABLE_CANDIDATE": 6
    },
    "regime_proxy": {
      "STABLE_CANDIDATE": 3
    },
    "trend_momentum": {
      "STABLE_CANDIDATE": 3
    },
    "volatility": {
      "STABLE_CANDIDATE": 1
    },
    "volume_liquidity": {
      "STABLE_CANDIDATE": 6
    }
  },
  "stable_candidate_count": 101,
  "stable_raw_candidate_features": [
    "model_name",
    "feature_set",
    "split_name",
    "avg_win_past_rebuilt",
    "avg_loss_past_rebuilt",
    "avg_win_past",
    "avg_loss_past",
    "cost_proxy_rebuilt",
    "cost_proxy",
    "ev_raw_proxy",
    "ev_proxy_ready",
    "payoff_estimate_ready",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "direction_up_after_cost_3bar",
    "direction_up_after_cost_6bar",
    "tp_before_sl_conservative",
    "derivatives_included",
    "macro_included",
    "derivatives_feature_status",
    "funding_rate_binance",
    "funding_rate_bybit",
    "long_short_ratio_binance",
    "open_interest_bybit",
    "premium_binance",
    "premium_bybit",
    "taker_buy_sell_ratio_binance",
    "taker_buy_volume_binance",
    "taker_sell_volume_binance",
    "funding_rate",
    "long_short_ratio",
    "open_interest",
    "premium",
    "taker_buy_sell_ratio",
    "taker_buy_volume",
    "taker_sell_volume",
    "timeframe_x",
    "feature_status",
    "funding_rate_mean",
    "funding_rate_spread_binance_bybit",
    "funding_rate_diff_binance_bybit",
    "funding_rate_zscore_30d",
    "funding_rate_zscore_90d",
    "funding_rate_change_1",
    "funding_rate_change_3",
    "funding_zscore_30d",
    "funding_zscore_90d"
  ],
  "stable_alpha_candidate_features": [
    "combined_alpha_score",
    "combined_alpha_score_no_derivatives",
    "combined_alpha_score_no_macro",
    "ohlcv_only_alpha_score",
    "macro_derivatives_score"
  ],
  "unstable_feature_count": 11,
  "recommended_raw_feature_families_for_v1_44": [
    "alpha_score_or_model_output"
  ],
  "recommended_alpha_feature_families_for_v1_44": [
    "alpha_score_or_model_output"
  ],
  "diagnostic_only_model_output_features": [
    "predicted_probability",
    "calibrated_probability_rebuilt",
    "calibrated_probability",
    "predicted_probability_calibrated"
  ],
  "avoid_feature_families_for_v1_44": [],
  "model_outputs_excluded_from_raw_feature_recommendations": true
}
```