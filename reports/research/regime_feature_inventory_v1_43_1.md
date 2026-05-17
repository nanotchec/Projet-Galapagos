# Regime Feature Inventory V1.43.1

Status: COMPLETE

### Summary
```json
{
  "inventory_status": "REGIME_FEATURE_INVENTORY_COMPLETE_WITH_OUTCOME_EXCLUSIONS",
  "total_columns": 139,
  "usable_feature_count": 48,
  "forbidden_outcome_columns": [
    "target",
    "predicted_label",
    "actual_target",
    "forward_return_6bar",
    "forward_return_12bar",
    "cost_adjusted_forward_return",
    "forward_return_1bar",
    "forward_return_3bar",
    "forward_return_6bar_ds",
    "forward_return_12bar_ds",
    "max_favorable_excursion_1bar",
    "max_adverse_excursion_1bar",
    "max_favorable_excursion_3bar",
    "max_adverse_excursion_3bar",
    "max_favorable_excursion_6bar",
    "max_adverse_excursion_6bar",
    "max_favorable_excursion_12bar",
    "max_adverse_excursion_12bar"
  ],
  "family_counts": {
    "unknown": 64,
    "alpha_score_or_model_output": 26,
    "target_outcome_forbidden": 18,
    "metadata": 9,
    "volume_liquidity": 6,
    "price_return": 6,
    "microstructure": 3,
    "trend_momentum": 3,
    "regime_proxy": 3,
    "volatility": 1
  },
  "usable_features": [
    "predicted_probability",
    "calibrated_probability_rebuilt",
    "calibrated_probability",
    "predicted_probability_calibrated",
    "volume",
    "taker_buy_volume_binance",
    "taker_sell_volume_binance",
    "taker_buy_volume",
    "taker_sell_volume",
    "funding_rate_spread_binance_bybit",
    "funding_rate_zscore_30d",
    "funding_rate_zscore_90d",
    "funding_rate_change_1",
    "funding_rate_change_3",
    "funding_zscore_30d",
    "funding_zscore_90d",
    "funding_trend_3",
    "open_interest_change_1",
    "open_interest_change_3",
    "open_interest_zscore_30d",
    "open_interest_zscore_90d",
    "oi_change_1",
    "oi_change_3",
    "oi_zscore_30d",
    "oi_zscore_90d",
    "premium_zscore_30d",
    "long_short_ratio_zscore",
    "taker_imbalance",
    "taker_imbalance_zscore",
    "derivatives_risk_regime",
    "derivatives_crowding_score",
    "derivatives_leverage_score",
    "derivatives_regime_score",
    "derivatives_score",
    "vol_regime_vix",
    "equity_market_trend",
    "macro_regime",
    "ohlcv_momentum_score",
    "ohlcv_breakout_score",
    "volatility_quality_score",
    "macro_regime_score",
    "cost_penalty_score",
    "volume_quality_score",
    "combined_alpha_score",
    "combined_alpha_score_no_derivatives",
    "combined_alpha_score_no_macro",
    "ohlcv_only_alpha_score",
    "macro_derivatives_score"
  ],
  "outcome_like_features_excluded": true,
  "outcome_like_feature_exclusion_count": 18,
  "all_metadata": [
    {
      "column": "timestamp",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "model_name",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "feature_set",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "target",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "split_name",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "predicted_probability",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "predicted_label",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "actual_target",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "forward_return_6bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "forward_return_12bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "cost_adjusted_forward_return",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "calibrated_probability_rebuilt",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "calibrated_probability",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "predicted_probability_calibrated",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "avg_win_past_rebuilt",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "avg_loss_past_rebuilt",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "avg_win_past",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "avg_loss_past",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "cost_proxy_rebuilt",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "cost_proxy",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "ev_calibrated_proxy_rebuilt",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "ev_calibrated_proxy",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "ev_raw_proxy",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "ev_proxy_ready",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "payoff_estimate_ready",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "open",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "high",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "low",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "close",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "volume",
      "family": "volume_liquidity",
      "is_usable": true
    },
    {
      "column": "forward_return_1bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "forward_return_3bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "forward_return_6bar_ds",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "forward_return_12bar_ds",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_favorable_excursion_1bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_adverse_excursion_1bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_favorable_excursion_3bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_adverse_excursion_3bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_favorable_excursion_6bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_adverse_excursion_6bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_favorable_excursion_12bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "max_adverse_excursion_12bar",
      "family": "target_outcome_forbidden",
      "is_usable": false
    },
    {
      "column": "direction_up_after_cost_3bar",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "direction_up_after_cost_6bar",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "tp_before_sl_conservative",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "derivatives_included",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "macro_included",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "derivatives_feature_status",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "derivatives_available_timestamp",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "funding_rate_binance",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "funding_rate_bybit",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "long_short_ratio_binance",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "open_interest_bybit",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "premium_binance",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "premium_bybit",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "taker_buy_sell_ratio_binance",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "taker_buy_volume_binance",
      "family": "volume_liquidity",
      "is_usable": true
    },
    {
      "column": "taker_sell_volume_binance",
      "family": "volume_liquidity",
      "is_usable": true
    },
    {
      "column": "funding_rate",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "long_short_ratio",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "open_interest",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "premium",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "taker_buy_sell_ratio",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "taker_buy_volume",
      "family": "volume_liquidity",
      "is_usable": true
    },
    {
      "column": "taker_sell_volume",
      "family": "volume_liquidity",
      "is_usable": true
    },
    {
      "column": "timeframe_x",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "feature_status",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "funding_rate_mean",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "funding_rate_spread_binance_bybit",
      "family": "microstructure",
      "is_usable": true
    },
    {
      "column": "funding_rate_diff_binance_bybit",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "funding_rate_zscore_30d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "funding_rate_zscore_90d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "funding_rate_change_1",
      "family": "price_return",
      "is_usable": true
    },
    {
      "column": "funding_rate_change_3",
      "family": "price_return",
      "is_usable": true
    },
    {
      "column": "funding_zscore_30d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "funding_zscore_90d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "funding_trend_3",
      "family": "trend_momentum",
      "is_usable": true
    },
    {
      "column": "funding_extreme_positive",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "funding_extreme_negative",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "open_interest_mean",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "open_interest_change_1",
      "family": "price_return",
      "is_usable": true
    },
    {
      "column": "open_interest_change_3",
      "family": "price_return",
      "is_usable": true
    },
    {
      "column": "open_interest_zscore_30d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "open_interest_zscore_90d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "oi_change_1",
      "family": "price_return",
      "is_usable": true
    },
    {
      "column": "oi_change_3",
      "family": "price_return",
      "is_usable": true
    },
    {
      "column": "oi_zscore_30d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "oi_zscore_90d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "premium_mean",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "premium_zscore_30d",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "basis_proxy",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "premium_proxy",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "long_short_ratio_zscore",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "taker_imbalance",
      "family": "microstructure",
      "is_usable": true
    },
    {
      "column": "taker_imbalance_zscore",
      "family": "microstructure",
      "is_usable": true
    },
    {
      "column": "long_short_crowding",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "price_oi_divergence",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "price_oi_confirmation",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "liquidation_proxy",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "derivatives_available_count",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "derivatives_missing_count",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "derivatives_confidence_score",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "derivatives_risk_regime",
      "family": "regime_proxy",
      "is_usable": true
    },
    {
      "column": "derivatives_crowding_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "derivatives_leverage_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "derivatives_regime_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "derivatives_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "available_timestamp",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "DFF",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "DGS10",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "DGS2",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "NASDAQCOM",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "SP500",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "T10Y2Y",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "VIXCLS",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "timeframe_y",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "yield_curve_slope",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "vol_regime_vix",
      "family": "regime_proxy",
      "is_usable": true
    },
    {
      "column": "rates_pressure",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "equity_market_trend",
      "family": "trend_momentum",
      "is_usable": true
    },
    {
      "column": "macro_regime",
      "family": "regime_proxy",
      "is_usable": true
    },
    {
      "column": "macro_confidence",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "macro_last_updated",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "ohlcv_momentum_score",
      "family": "trend_momentum",
      "is_usable": true
    },
    {
      "column": "ohlcv_breakout_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "volatility_quality_score",
      "family": "volatility",
      "is_usable": true
    },
    {
      "column": "macro_regime_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "cost_penalty_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "crowded_trade_penalty",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "missing_data_penalty",
      "family": "unknown",
      "is_usable": false
    },
    {
      "column": "volume_quality_score",
      "family": "volume_liquidity",
      "is_usable": true
    },
    {
      "column": "combined_alpha_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "combined_alpha_score_no_derivatives",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "combined_alpha_score_no_macro",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "ohlcv_only_alpha_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "macro_derivatives_score",
      "family": "alpha_score_or_model_output",
      "is_usable": true
    },
    {
      "column": "timestamp_year",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "timestamp_half",
      "family": "metadata",
      "is_usable": false
    },
    {
      "column": "period",
      "family": "metadata",
      "is_usable": false
    }
  ]
}
```