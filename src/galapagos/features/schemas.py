from __future__ import annotations

FEATURE_COLUMNS_V2_5 = [
    # metadata
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "available_ts",
    "decision_ts",
    "feature_available_ts",
    "ingested_at_ts",
    "feature_run_id",
    "source_ohlcv_sha256",
    "feature_schema_version",
    # prix / returns passés
    "close_lag_1",
    "return_1",
    "log_return_1",
    "return_3",
    "log_return_3",
    "return_5",
    "log_return_5",
    # volatilité passée
    "rolling_vol_5",
    "rolling_vol_15",
    "rolling_vol_30",
    # range / candle
    "candle_range",
    "candle_body",
    "upper_wick",
    "lower_wick",
    "close_position_in_range",
    # volume
    "volume_lag_1",
    "volume_return_1",
    "rolling_volume_mean_5",
    "rolling_volume_mean_15",
    "rolling_volume_zscore_15",
    # trend / distance
    "sma_5",
    "sma_15",
    "sma_30",
    "close_to_sma_5",
    "close_to_sma_15",
    "close_to_sma_30",
    # temporal
    "hour_utc",
    "day_of_week_utc",
    "is_weekend_utc",
    # quality
    "warmup_row",
    "feature_null_count",
    "feature_error_count",
]

FORBIDDEN_TERMS = [
    "future",
    "label",
    "target",
    "pnl",
    "profit",
    "return_forward",
    "forward_return",
    "y",
    "signal",
    "strategy",
    "order",
    "trade_decision",
    "prediction",
    "predicted",
    "score_ml",
    "model_score",
    "alpha",
]
