from __future__ import annotations


VERSION = "V9.54"
SOURCE = "binance_archive"
VENUE = "binance"
MARKET_TYPE = "futures_um"
SYMBOL = "BTCUSDT"
TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
EXPECTED_TIMEFRAMES = ["1m", "5m", "15m", "1h"]
EXPECTED_ROWS_BY_TIMEFRAME = {
    "1m": 2_630_880,
    "5m": 526_176,
    "15m": 175_392,
    "1h": 43_848,
}
FEATURE_SCHEMA_VERSION = "derivatives_funding_oi_features_v9_54_v1"

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
    "derivatives_feature_run_id",
    "derivatives_feature_schema_version",
    "source_collection_version",
    "source_window_start",
    "source_window_end",
    "actual_window_start",
    "actual_window_end",
]

FUNDING_FEATURE_COLUMNS = [
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
    "hours_to_next_funding_known_schedule",
    "funding_missing_flag",
]

OI_FEATURE_COLUMNS = [
    "open_interest_current",
    "open_interest_change_1",
    "open_interest_pct_change_1",
    "open_interest_rolling_mean",
    "open_interest_rolling_zscore_past",
    "oi_missing_flag",
]

MARK_PREMIUM_FEATURE_COLUMNS = [
    "mark_price_basis_to_spot",
    "premium_index",
    "premium_index_rolling_mean",
    "premium_missing_flag",
]

FEATURE_COLUMNS = FUNDING_FEATURE_COLUMNS + OI_FEATURE_COLUMNS + MARK_PREMIUM_FEATURE_COLUMNS

AUDIT_COLUMNS = [
    "row_valid_for_derivatives_features",
    "derivatives_feature_null_count",
    "derivatives_feature_error_count",
    "derivatives_feature_invalid_reason",
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
