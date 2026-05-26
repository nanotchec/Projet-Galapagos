from __future__ import annotations

from pathlib import Path


VERSION_V9_0 = "V9.0"
TIMEFRAMES_V9_0 = ["1m", "5m", "15m", "1h"]
WINDOW_START_V9_0 = "2023-03-25"
WINDOW_END_V9_0 = "2024-03-24"
TOTAL_DAYS_V9_0 = 366
EXPECTED_ROWS_V9_0 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}

FEATURE_SELECTION_JSON_V8_9 = Path("reports/features/ohlcv_trades_feature_selection_v8_9.json")
FEATURE_AUDIT_MANIFEST_V8_9 = Path("reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json")
INPUT_FEATURE_MANIFEST_V8_3 = Path("reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json")

MANIFEST_PATH_V9_0 = Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json")
REPORT_JSON_PATH_V9_0 = Path("reports/features/refined_ohlcv_trades_feature_store_v9_0.json")
REPORT_MD_PATH_V9_0 = Path("reports/features/refined_ohlcv_trades_feature_store_v9_0.md")
DOC_PATH_V9_0 = Path("docs/refined_ohlcv_trades_feature_store_v9_0.md")

FEATURE_SCHEMA_VERSION_V9_0 = "REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0"
REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0 = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count_ohlcv",
    "agg_trade_count",
    "agg_trade_quantity_sum",
    "agg_trade_quote_quantity_sum",
    "agg_trade_vwap",
    "taker_buy_ratio_count",
    "taker_buy_ratio_quantity",
    "taker_imbalance_quantity",
    "agg_trades_per_minute",
    "trade_flow_pressure",
    "hour_utc",
    "day_of_week_utc",
]

REFINED_OHLCV_TRADES_METADATA_COLUMNS_V9_0 = [
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
    "feature_run_id",
    "source_ohlcv_sha256",
    "source_trades_manifest_sha256",
    "source_v8_3_features_sha256",
    "source_feature_selection_sha256",
    "trade_source_type",
    "feature_schema_version",
]
REFINED_OHLCV_TRADES_AUDIT_COLUMNS_V9_0 = [
    "warmup_row",
    "refined_feature_null_count",
    "refined_feature_error_count",
]
REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0 = [
    *REFINED_OHLCV_TRADES_METADATA_COLUMNS_V9_0,
    *REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0,
    *REFINED_OHLCV_TRADES_AUDIT_COLUMNS_V9_0,
]

FORBIDDEN_REFINED_FEATURE_TERMS_V9_0 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
    "target",
    "prediction",
    "signal",
    "trading_signal",
    "strategy",
    "order",
    "pnl",
    "profit",
    "backtest",
    "position_size",
]

SAFETY_FLAGS_V9_0 = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "ml_enabled": False,
    "labels_enabled": False,
    "dataset_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}

EXPECTED_LIMITATIONS_V9_0 = [
    "V9.0 produit uniquement une feature store raffinee a partir des features V8.3 et de la selection V8.9.",
    "V9.0 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]


def get_refined_feature_path_v9_0(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_0/features/refined_ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_0}_{WINDOW_END_V9_0}"
        / "features.parquet"
    )
