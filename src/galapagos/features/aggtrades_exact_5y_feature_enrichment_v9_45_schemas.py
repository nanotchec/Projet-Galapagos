from __future__ import annotations

TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
EXPECTED_DAYS = 1827
EXPECTED_TIMEFRAMES = ("1m", "5m", "15m", "1h")
EXPECTED_ROWS_BY_TIMEFRAME = {
    "1m": 2_630_880,
    "5m": 526_176,
    "15m": 175_392,
    "1h": 43_848,
}

SOURCE = "binance_archive"
VENUE = "binance"
MARKET_TYPE = "spot"
SYMBOL = "BTCUSDT"
FEATURE_SCHEMA_VERSION = "aggtrades_exact_5y_features_v9_45_v1"
SOURCE_AGGTRADES_VALIDATION_VERSION = "V9.32"

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
    "feature_run_id",
    "feature_schema_version",
    "source_aggtrades_validation_version",
    "source_window_start",
    "source_window_end",
    "quantile_threshold_method",
]

COUNT_FEATURE_COLUMNS = [
    "agg_trade_count_exact",
    "taker_buy_count_exact",
    "taker_sell_count_exact",
    "buyer_maker_true_count_exact",
    "buyer_maker_false_count_exact",
]

VOLUME_FEATURE_COLUMNS = [
    "agg_trade_volume_exact",
    "agg_trade_quote_volume_exact",
    "taker_buy_base_volume_exact",
    "taker_sell_base_volume_exact",
    "taker_buy_quote_volume_exact",
    "taker_sell_quote_volume_exact",
]

IMBALANCE_FEATURE_COLUMNS = [
    "taker_buy_sell_count_imbalance_exact",
    "taker_buy_sell_volume_imbalance_exact",
    "taker_buy_ratio_exact",
    "taker_sell_ratio_exact",
]

TRADE_SIZE_FEATURE_COLUMNS = [
    "average_trade_size_exact",
    "median_trade_size_exact",
    "p75_trade_size_exact",
    "p90_trade_size_exact",
    "p95_trade_size_exact",
    "p99_trade_size_exact",
    "max_trade_size_exact",
    "large_trade_count_p95_exact",
    "large_trade_volume_p95_exact",
    "large_trade_count_p99_exact",
    "large_trade_volume_p99_exact",
]

DISTRIBUTION_FEATURE_COLUMNS = [
    "trade_size_bucket_small_count",
    "trade_size_bucket_medium_count",
    "trade_size_bucket_large_count",
    "trade_size_bucket_whale_count",
]

BURST_FEATURE_COLUMNS = [
    "agg_trade_count_per_second_mean",
    "agg_trade_count_per_second_max",
    "max_trades_in_1s",
    "max_volume_in_1s",
    "burst_count_1s_p95",
    "burst_volume_1s_p95",
]

TIMING_FEATURE_COLUMNS = [
    "first_trade_ts",
    "last_trade_ts",
    "active_seconds_count",
    "active_seconds_ratio",
    "seconds_since_previous_trade_bucket_start",
    "seconds_to_last_trade_bucket_end",
]

MISSINGNESS_FEATURE_COLUMNS = [
    "no_trade_bucket",
    "aggtrades_missing_flag",
    "aggtrades_partial_bucket_flag",
    "exact_feature_error_count",
    "exact_feature_null_count",
]

ROLLING_FEATURE_COLUMNS = [
    "rolling_exact_trade_count_mean_5",
    "rolling_exact_trade_count_mean_15",
    "rolling_exact_trade_count_mean_60",
    "rolling_exact_taker_imbalance_mean_5",
    "rolling_exact_taker_imbalance_mean_15",
    "rolling_exact_taker_imbalance_mean_60",
    "rolling_large_trade_count_mean_5",
    "rolling_large_trade_count_mean_15",
    "rolling_large_trade_count_mean_60",
]

FEATURE_COLUMNS = (
    COUNT_FEATURE_COLUMNS
    + VOLUME_FEATURE_COLUMNS
    + IMBALANCE_FEATURE_COLUMNS
    + TRADE_SIZE_FEATURE_COLUMNS
    + DISTRIBUTION_FEATURE_COLUMNS
    + BURST_FEATURE_COLUMNS
    + TIMING_FEATURE_COLUMNS
    + MISSINGNESS_FEATURE_COLUMNS
    + ROLLING_FEATURE_COLUMNS
)

AUDIT_COLUMNS = [
    "row_valid_for_exact_features",
    "feature_invalid_reason",
]

STRICT_COLUMNS = METADATA_COLUMNS + FEATURE_COLUMNS + AUDIT_COLUMNS

FEATURE_FAMILIES = {
    "counts": COUNT_FEATURE_COLUMNS,
    "volumes": VOLUME_FEATURE_COLUMNS,
    "imbalances": IMBALANCE_FEATURE_COLUMNS,
    "trade_size": TRADE_SIZE_FEATURE_COLUMNS,
    "distribution_buckets": DISTRIBUTION_FEATURE_COLUMNS,
    "burst_intensity": BURST_FEATURE_COLUMNS,
    "timing": TIMING_FEATURE_COLUMNS,
    "missingness_audit": MISSINGNESS_FEATURE_COLUMNS,
    "rolling_past_only": ROLLING_FEATURE_COLUMNS,
}

FORBIDDEN_FEATURE_COLUMNS = {
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
    "entry",
    "exit",
    "trade_decision",
    "label",
    "target",
    "future",
}
