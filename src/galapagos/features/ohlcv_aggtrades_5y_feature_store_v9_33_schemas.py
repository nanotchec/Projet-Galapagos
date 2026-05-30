from __future__ import annotations

TARGET_5Y_WINDOW_START = "2021-05-05"
TARGET_5Y_WINDOW_END = "2026-05-05"
EXPECTED_TIMEFRAMES = ("1m", "5m", "15m", "1h")
SYMBOL = "BTCUSDT"
MARKET_TYPE = "spot"
SOURCE = "binance_archive"

FORBIDDEN_FEATURE_COLUMNS = {
    "future",
    "future_return",
    "label",
    "target",
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
}

READINESS_REQUIRED_REPORT_KEYS = {
    "version",
    "source_version",
    "decision",
    "ohlcv_readiness",
    "aggtrades_readiness",
    "feature_store_created",
    "features_created",
    "quality_status",
    "safety_flags",
}
