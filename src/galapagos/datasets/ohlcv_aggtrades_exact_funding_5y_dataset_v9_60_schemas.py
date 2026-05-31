from __future__ import annotations

from pathlib import Path

from galapagos.features.ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_schemas import FEATURE_COLUMNS


VERSION = "V9.60"
SOURCE_VERSION = "V9.59"
DIRECTION = "ohlcv_aggtrades_exact_funding_5y_dataset"
TARGET_WINDOW_START = "2021-05-05T00:00:00Z"
TARGET_WINDOW_END = "2026-04-30T16:00:00Z"
COMMON_WINDOW_LABEL = "2021-05-05_to_2026-04-30T16-00-00Z"
TIMEFRAMES = ("1m", "5m", "15m", "1h")
TIMEFRAME_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}

SOURCE_FEATURE_STORE_VERSION = "V9.59"
SOURCE_FEATURE_VALIDATION_VERSION = "V9.59"
SOURCE_LABEL_VERSION = "V9.40"
DATASET_SCHEMA_VERSION = "OHLCV_AGGTRADES_EXACT_FUNDING_5Y_DATASET_V9_60"
DATASET_RUN_ID_PREFIX = "v9_60"
SELECTED_PRIMARY_LABEL = "up_down_flat_volnorm_h1_5y"
DIAGNOSTIC_LABELS = ("up_down_flat_volnorm_h4_5y", "binary_directional_volnorm_h4_5y")
LABEL_COLUMNS = (SELECTED_PRIMARY_LABEL, *DIAGNOSTIC_LABELS, "label_valid", "label_invalid_reason")

FEATURE_BASE_PATH = Path("data/research/v9_59/features/ohlcv_aggtrades_exact_funding_5y_common_window/source=binance_archive/market_type=mixed_spot_futures_um/symbol=BTCUSDT")
LABEL_BASE_PATH = Path("data/research/v9_40/labels/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
DATASET_BASE_PATH = Path("data/research/v9_60/datasets/ohlcv_aggtrades_exact_funding_5y_common_window/source=binance_archive/market_type=mixed_spot_futures_um/symbol=BTCUSDT")

REPORT_JSON_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.json")
REPORT_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.md")
DATACARD_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_datacard.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.md")

INPUT_PATHS = {
    "v9_59_feature_store": Path("reports/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.json"),
    "v9_59_manifest": Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_manifest.json"),
    "v9_40_label_factory": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
}

SPLIT_POLICY = {
    "shuffle": False,
    "train_ratio": 0.60,
    "validation_ratio": 0.20,
    "test_ratio": 0.20,
    "walk_forward_group": "calendar_month",
    "purge_embargo_group": "none_v9_60_preview",
}

FEATURE_AUDIT_COLUMNS = [
    "warmup_row",
    "zero_trade_bucket",
    "feature_null_count",
    "feature_error_count",
    "combined_feature_null_count",
    "combined_feature_error_count",
    "row_valid_for_combined_features",
    "combined_feature_invalid_reason",
    "row_valid_for_funding_features",
    "funding_feature_null_count",
    "funding_feature_error_count",
    "funding_feature_invalid_reason",
    "row_valid_for_funding_common_features",
    "funding_common_feature_null_count",
    "funding_common_feature_error_count",
    "funding_common_feature_invalid_reason",
]

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
    "purge_embargo_group",
    "dataset_run_id",
    "dataset_schema_version",
    "funding_common_feature_schema_version",
    "label_schema_version",
    "source_combined_feature_store_version",
    "source_combined_feature_validation_version",
    "source_label_version",
    "target_name",
    "selected_primary_label",
    *FEATURE_COLUMNS,
    *LABEL_COLUMNS,
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
    "funding_common_window_dataset_created",
    "funding_common_window_dataset_created_with_warnings",
    "funding_common_window_dataset_blocked_by_feature_quality",
    "funding_common_window_dataset_blocked_by_label_quality",
    "funding_common_window_dataset_blocked_by_leakage",
    "funding_common_window_dataset_partial",
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
    "ml_executed": False,
}
