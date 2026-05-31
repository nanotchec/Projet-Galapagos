from __future__ import annotations

from pathlib import Path

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import AUDIT_COLUMNS as FEATURE_AUDIT_COLUMNS
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import FEATURE_COLUMNS
from galapagos.labels.redesigned_5y_label_factory_v9_64_schemas import LABEL_COLUMNS, SELECTED_PRIMARY_LABEL


VERSION = "V9.65"
SOURCE_VERSION = "V9.64"
DIRECTION = "redesigned_label_5y_dataset"
WINDOW_LABEL = "2021-05-05_2026-05-05"
TIMEFRAMES = ("1m", "5m", "15m", "1h")
SOURCE_FEATURE_STORE_VERSION = "V9.47"
SOURCE_LABEL_VERSION = "V9.64"
DATASET_SCHEMA_VERSION = "REDESIGNED_LABEL_5Y_DATASET_V9_65"
DATASET_RUN_ID_PREFIX = "v9_65"

FEATURE_BASE_PATH = Path("data/research/v9_47/features/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
LABEL_BASE_PATH = Path("data/research/v9_64/labels/redesigned_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
DATASET_BASE_PATH = Path("data/research/v9_65/datasets/redesigned_label_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")

REPORT_JSON_PATH = Path("reports/datasets/redesigned_label_5y_dataset_v9_65.json")
REPORT_MD_PATH = Path("reports/datasets/redesigned_label_5y_dataset_v9_65.md")
DATACARD_MD_PATH = Path("reports/datasets/redesigned_label_5y_dataset_v9_65_datacard.md")
MANIFEST_PATH = Path("reports/manifests/redesigned_label_5y_dataset_v9_65_manifest.json")

INPUT_PATHS = {
    "v9_64_label_factory": Path("reports/labels/redesigned_5y_label_factory_v9_64.json"),
    "v9_47_feature_store": Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
}

SPLIT_POLICY = {"shuffle": False, "train_ratio": 0.60, "validation_ratio": 0.20, "test_ratio": 0.20, "walk_forward_group": "calendar_month"}

DATASET_COLUMNS = [
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
    "label_available_ts",
    "split",
    "walk_forward_group",
    "dataset_run_id",
    "dataset_schema_version",
    "combined_feature_schema_version",
    "label_schema_version",
    "source_feature_store_version",
    "source_label_version",
    "target_name",
    "selected_primary_label",
    *FEATURE_COLUMNS,
    *LABEL_COLUMNS,
    "label_valid",
    "label_invalid_reason",
    "row_valid_for_dataset",
    "dataset_null_count",
    "dataset_error_count",
    "dataset_invalid_reason",
    *FEATURE_AUDIT_COLUMNS,
    "label_null_count",
    "label_error_count",
]

FORBIDDEN_COLUMNS = {
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

ALLOWED_DECISIONS = {
    "redesigned_label_dataset_created",
    "redesigned_label_dataset_created_with_warnings",
    "redesigned_label_dataset_blocked_by_quality",
    "redesigned_label_dataset_blocked_by_leakage",
    "redesigned_label_dataset_partial",
}

FINDINGS = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_ml": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}
