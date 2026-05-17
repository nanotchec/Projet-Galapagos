# Regime Feature Stability Scorecard V1.43.4

Status: COMPLETE

### Summary
```json
{
  "feature_stability_scorecard_status": "FEATURE_STABILITY_SCORECARD_COMPLETE",
  "family_summary": {
    "alpha_score_family": {
      "STABLE_CANDIDATE": 22
    },
    "metadata": {
      "STABLE_CANDIDATE": 9
    },
    "microstructure": {
      "STABLE_CANDIDATE": 3
    },
    "model_output_family": {
      "STABLE_CANDIDATE": 4
    },
    "price_return": {
      "STABLE_CANDIDATE": 6
    },
    "regime_proxy": {
      "STABLE_CANDIDATE": 3
    },
    "target_outcome_forbidden": {
      "STABLE_CANDIDATE": 18
    },
    "trend_momentum": {
      "STABLE_CANDIDATE": 3
    },
    "unknown": {
      "STABLE_CANDIDATE": 64
    },
    "volatility": {
      "STABLE_CANDIDATE": 1
    },
    "volume_liquidity": {
      "STABLE_CANDIDATE": 6
    }
  },
  "stable_candidate_count": 82,
  "stable_raw_candidate_features": [
    "open",
    "high",
    "low",
    "close",
    "volume",
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
    "feature_status",
    "funding_rate_mean",
    "funding_rate_spread_binance_bybit",
    "funding_rate_diff_binance_bybit",
    "funding_rate_zscore_30d",
    "funding_rate_zscore_90d",
    "funding_rate_change_1",
    "funding_rate_change_3",
    "funding_zscore_30d",
    "funding_zscore_90d",
    "funding_trend_3",
    "funding_extreme_positive",
    "funding_extreme_negative",
    "open_interest_mean",
    "open_interest_change_1",
    "open_interest_change_3",
    "open_interest_zscore_30d",
    "open_interest_zscore_90d",
    "oi_change_1",
    "oi_change_3",
    "oi_zscore_30d",
    "oi_zscore_90d",
    "premium_mean",
    "premium_zscore_30d",
    "long_short_ratio_zscore",
    "taker_imbalance"
  ],
  "stable_alpha_candidate_features": [
    "volatility_quality_score",
    "volume_quality_score",
    "combined_alpha_score",
    "combined_alpha_score_no_derivatives",
    "combined_alpha_score_no_macro",
    "ohlcv_only_alpha_score",
    "macro_derivatives_score"
  ],
  "unstable_feature_count": 57,
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
  "avoid_feature_families_for_v1_44": [],
  "model_outputs_excluded_from_raw_feature_recommendations": true,
  "ev_proxies_excluded_from_raw_feature_recommendations": true,
  "metadata_excluded_from_raw_feature_recommendations": true,
  "alpha_score_or_model_output_removed": true
}
```