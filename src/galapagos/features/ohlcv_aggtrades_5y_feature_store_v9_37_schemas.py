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
FEATURE_SCHEMA_VERSION = "ohlcv_aggtrades_5y_features_v9_37_v1"
OHLCV_SOURCE_TYPE = "derived_from_aggtrades"
AGGTRADES_SOURCE_TYPE = "binance_public_archive_aggtrades"
SOURCE_OHLCV_VALIDATION_VERSION = "V9.36"
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
    "ohlcv_source_type",
    "aggtrades_source_type",
    "source_ohlcv_validation_version",
    "source_aggtrades_validation_version",
    "source_window_start",
    "source_window_end",
]

AUDIT_COLUMNS = [
    "warmup_row",
    "zero_trade_bucket",
    "feature_null_count",
    "feature_error_count",
    "row_valid_for_features",
    "feature_invalid_reason",
]

FEATURE_COLUMNS = [
    "close_return_1",
    "log_return_1",
    "rolling_return_5",
    "rolling_return_15",
    "rolling_return_60",
    "rolling_volatility_5",
    "rolling_volatility_15",
    "rolling_volatility_60",
    "high_low_range",
    "close_open_return",
    "candle_body",
    "upper_wick",
    "lower_wick",
    "volume",
    "quote_volume",
    "trades_count",
    "volume_rolling_mean_5",
    "volume_rolling_mean_15",
    "volume_rolling_mean_60",
    "volume_rolling_std_5",
    "volume_rolling_std_15",
    "volume_rolling_std_60",
    "zero_trade_bucket_rolling_count_60",
    "agg_trade_count",
    "agg_trade_volume",
    "agg_trade_quote_volume",
    "average_trade_size",
    "taker_buy_base_volume",
    "taker_sell_base_volume",
    "taker_buy_ratio",
    "taker_buy_sell_imbalance",
    "trade_intensity_rolling_5",
    "trade_intensity_rolling_15",
    "trade_intensity_rolling_60",
    "agg_trade_volume_rolling_mean_5",
    "agg_trade_volume_rolling_mean_15",
    "agg_trade_volume_rolling_mean_60",
    "taker_imbalance_rolling_mean_5",
    "taker_imbalance_rolling_mean_15",
    "taker_imbalance_rolling_mean_60",
    "missing_aggtrades_flag",
]

STRICT_COLUMNS = METADATA_COLUMNS + FEATURE_COLUMNS + AUDIT_COLUMNS

FEATURE_FAMILIES = {
    "ohlcv_returns": [
        "close_return_1",
        "log_return_1",
        "rolling_return_5",
        "rolling_return_15",
        "rolling_return_60",
        "rolling_volatility_5",
        "rolling_volatility_15",
        "rolling_volatility_60",
    ],
    "ohlcv_candle": [
        "high_low_range",
        "close_open_return",
        "candle_body",
        "upper_wick",
        "lower_wick",
    ],
    "ohlcv_volume": [
        "volume",
        "quote_volume",
        "trades_count",
        "volume_rolling_mean_5",
        "volume_rolling_mean_15",
        "volume_rolling_mean_60",
        "volume_rolling_std_5",
        "volume_rolling_std_15",
        "volume_rolling_std_60",
    ],
    "zero_trade": [
        "zero_trade_bucket",
        "zero_trade_bucket_rolling_count_60",
    ],
    "aggtrades_aggregates": [
        "agg_trade_count",
        "agg_trade_volume",
        "agg_trade_quote_volume",
        "average_trade_size",
        "taker_buy_base_volume",
        "taker_sell_base_volume",
        "taker_buy_ratio",
        "taker_buy_sell_imbalance",
        "trade_intensity_rolling_5",
        "trade_intensity_rolling_15",
        "trade_intensity_rolling_60",
        "agg_trade_volume_rolling_mean_5",
        "agg_trade_volume_rolling_mean_15",
        "agg_trade_volume_rolling_mean_60",
        "taker_imbalance_rolling_mean_5",
        "taker_imbalance_rolling_mean_15",
        "taker_imbalance_rolling_mean_60",
        "missing_aggtrades_flag",
    ],
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
