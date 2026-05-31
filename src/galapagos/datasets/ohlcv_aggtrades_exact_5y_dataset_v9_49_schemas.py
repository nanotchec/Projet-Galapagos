from __future__ import annotations

from pathlib import Path

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import FEATURE_COLUMNS


VERSION = "V9.49"
SOURCE_VERSION = "V9.48"
LAST_VALIDATED_VERSION = "V9.48"
DIRECTION = "ohlcv_aggtrades_exact_5y_dataset"

TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
TOTAL_DAYS = 1827
TIMEFRAMES = ("1m", "5m", "15m", "1h")
TIMEFRAME_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
EXPECTED_ROWS = {
    "1m": 2_630_880,
    "5m": 526_176,
    "15m": 175_392,
    "1h": 43_848,
}

SOURCE_FEATURE_STORE_VERSION = "V9.47"
SOURCE_FEATURE_VALIDATION_VERSION = "V9.48"
SOURCE_LABEL_VERSION = "V9.40"
DATASET_SCHEMA_VERSION = "OHLCV_AGGTRADES_EXACT_5Y_DATASET_V9_49"
DATASET_RUN_ID_PREFIX = "v9_49"
SELECTED_PRIMARY_LABEL = "up_down_flat_volnorm_h1_5y"
DIAGNOSTIC_LABELS = ("up_down_flat_volnorm_h4_5y", "binary_directional_volnorm_h4_5y")
LABEL_COLUMNS = (SELECTED_PRIMARY_LABEL, *DIAGNOSTIC_LABELS, "label_valid", "label_invalid_reason")

FEATURE_BASE_PATH = Path("data/research/v9_47/features/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
LABEL_BASE_PATH = Path("data/research/v9_40/labels/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
DATASET_BASE_PATH = Path("data/research/v9_49/datasets/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")

REPORT_JSON_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.json")
REPORT_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.md")
DATACARD_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49_datacard.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_5y_dataset_v9_49_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_5y_dataset_v9_49.md")

INPUT_PATHS = {
    "v9_40_label_factory": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
    "v9_40_label_factory_md": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.md"),
    "v9_40_label_datacard": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40_datacard.md"),
    "v9_40_label_distribution": Path("reports/labels/ohlcv_aggtrades_5y_label_distribution_v9_40.json"),
    "v9_40_label_stability": Path("reports/labels/ohlcv_aggtrades_5y_label_stability_v9_40.json"),
    "v9_40_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_label_factory_v9_40_manifest.json"),
    "v9_48_feature_validation": Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json"),
    "v9_47_feature_store": Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.json"),
    "v9_48_manifest": Path("reports/manifests/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_manifest.json"),
    "v9_47_manifest": Path("reports/manifests/ohlcv_aggtrades_exact_5y_feature_store_v9_47_manifest.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

SPLIT_POLICY = {
    "shuffle": False,
    "train_ratio": 0.60,
    "validation_ratio": 0.20,
    "test_ratio": 0.20,
    "walk_forward_group": "calendar_month",
    "purge_embargo_group": "none_v9_49_preview",
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
    "combined_feature_schema_version",
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
    "feature_null_count",
    "feature_error_count",
    "combined_feature_null_count",
    "combined_feature_error_count",
    "label_null_count",
    "label_error_count",
    "warmup_row",
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
    "combined_features_5y_dataset_created",
    "combined_features_5y_dataset_created_with_warnings",
    "combined_features_5y_dataset_blocked_by_label_quality",
    "combined_features_5y_dataset_blocked_by_feature_quality",
    "combined_features_5y_dataset_blocked_by_leakage",
    "combined_features_5y_dataset_partial",
    "stop_combined_features_5y_dataset_branch",
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
