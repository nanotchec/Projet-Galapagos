from __future__ import annotations


AGG_TRADE_COLUMNS_V7_0 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "trade_source_type",
    "aggregate_trade_id",
    "price",
    "quantity",
    "first_trade_id",
    "last_trade_id",
    "event_ts",
    "trade_ts",
    "available_ts",
    "decision_ts",
    "is_buyer_maker",
    "is_best_match",
    "raw_file_sha256",
    "ingestion_run_id",
    "schema_version",
]

BINANCE_AGG_TRADE_RAW_COLUMNS = [
    "aggregate_trade_id",
    "price",
    "quantity",
    "first_trade_id",
    "last_trade_id",
    "trade_time",
    "is_buyer_maker",
    "is_best_match",
]

FORBIDDEN_TRADE_COLUMNS_V7_0 = {
    "future_return",
    "label",
    "target",
    "signal",
    "strategy",
    "order",
    "prediction",
    "pnl",
    "backtest",
    "trading_signal",
    "position_size",
    "profit",
}
