from __future__ import annotations

LABEL_COLUMNS_V2_6 = [
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
    "label_available_ts",
    "label_run_id",
    "source_ohlcv_sha256",
    "label_schema_version",
    # horizon 1
    "future_close_h1",
    "future_log_return_h1",
    "future_simple_return_h1",
    "direction_h1",
    "up_down_flat_h1",
    "label_end_ts_h1",
    "label_valid_h1",
    # horizon 3
    "future_close_h3",
    "future_log_return_h3",
    "future_simple_return_h3",
    "direction_h3",
    "up_down_flat_h3",
    "label_end_ts_h3",
    "label_valid_h3",
    # horizon 5
    "future_close_h5",
    "future_log_return_h5",
    "future_simple_return_h5",
    "direction_h5",
    "up_down_flat_h5",
    "label_end_ts_h5",
    "label_valid_h5",
    # quality
    "label_null_count",
    "label_error_count",
    "tail_row",
]

LABEL_COLUMNS_V3_1 = LABEL_COLUMNS_V2_6.copy()

FORBIDDEN_COLUMNS_V2_6 = [
    "signal",
    "strategy",
    "order",
    "trade_decision",
    "prediction",
    "predicted",
    "score_ml",
    "model_score",
    "alpha",
    "pnl",
    "profit",
    "backtest",
    "position_size",
    "execution",
]

FORBIDDEN_COLUMNS_V3_1 = FORBIDDEN_COLUMNS_V2_6.copy()
