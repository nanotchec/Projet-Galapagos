from __future__ import annotations


VERSION = "V9.57"
SOURCE = "binance_archive"
VENUE = "binance"
MARKET_TYPE = "futures_um"
SYMBOL = "BTCUSDT"
EXPECTED_TIMEFRAMES = ["1m", "5m", "15m", "1h"]
FEATURE_SCHEMA_VERSION = "funding_only_features_v9_57_v1"

METADATA_COLUMNS = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "open_ts",
    "close_ts",
    "decision_ts",
    "available_ts",
    "feature_available_ts",
    "funding_feature_run_id",
    "funding_feature_schema_version",
    "source_collection_version",
    "source_window_start",
    "source_window_end",
    "actual_window_start",
    "actual_window_end",
    "common_window_policy",
]

FEATURE_COLUMNS = [
    "funding_rate_current",
    "funding_rate_last",
    "funding_rate_change_1",
    "funding_rate_abs",
    "funding_rate_sign",
    "funding_rate_rolling_mean_3",
    "funding_rate_rolling_mean_9",
    "funding_rate_rolling_std_9",
    "funding_rate_zscore_past",
    "funding_rate_positive_streak",
    "funding_rate_negative_streak",
    "hours_since_last_funding",
    "funding_missing_flag",
    "funding_interval_gap_flag",
]

AUDIT_COLUMNS = [
    "row_valid_for_funding_features",
    "funding_feature_null_count",
    "funding_feature_error_count",
    "funding_feature_invalid_reason",
]

STRICT_COLUMNS = METADATA_COLUMNS + FEATURE_COLUMNS + AUDIT_COLUMNS

FORBIDDEN_FEATURE_TOKENS = {
    "prediction",
    "model_score",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "sharpe",
    "drawdown",
    "equity_curve",
    "profit_factor",
    "backtest",
    "position_size",
    "strategy",
    "label",
    "target",
    "future_return",
    "next_return",
}
