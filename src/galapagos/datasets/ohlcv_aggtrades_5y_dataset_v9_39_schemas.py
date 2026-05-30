from __future__ import annotations

from pathlib import Path


VERSION = "V9.39"
SOURCE_VERSION = "V9.38"
LAST_VALIDATED_VERSION = "V9.38"
DIRECTION = "ohlcv_aggtrades_5y_dataset"

TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
TOTAL_DAYS = 1827
TIMEFRAMES = ("1m", "5m", "15m", "1h")
EXPECTED_FEATURE_ROWS = {
    "1m": 2_630_880,
    "5m": 526_176,
    "15m": 175_392,
    "1h": 43_848,
}
FEATURE_COLUMNS_COUNT = 41

REPORT_JSON_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_39.json")
REPORT_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_39.md")
DATACARD_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_39_datacard.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_dataset_v9_39_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_dataset_v9_39.md")

DATASET_SCHEMA_VERSION = "OHLCV_AGGTRADES_5Y_DATASET_V9_39_PREVIEW_BLOCKED"
TARGET_NAME = None
SPLIT_POLICY = {
    "shuffle": False,
    "train_ratio": 0.60,
    "validation_ratio": 0.20,
    "test_ratio": 0.20,
    "walk_forward_group": "calendar_month",
    "purge_embargo_group": "none_v9_39_preview",
}

MINIMAL_DATASET_COLUMNS = [
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
    "feature_schema_version",
    "label_schema_version",
    "source_feature_store_version",
    "source_label_version",
    "row_valid_for_dataset",
    "dataset_null_count",
    "dataset_error_count",
    "dataset_invalid_reason",
]

FORBIDDEN_DATASET_COLUMNS = {
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

LABEL_CANDIDATE_REPORTS = {
    "max_history_v5_2": Path("reports/labels/max_history_label_factory_v5_2.json"),
    "volnorm_v9_6": Path("reports/labels/refined_volatility_normalized_labels_v9_6.json"),
    "horizon_event_v9_12": Path("reports/labels/horizon_event_label_redesign_v9_12.json"),
    "h4_dataset_v9_13": Path("reports/datasets/h4_label_candidate_dataset_v9_13.json"),
    "v9_11_failure_analysis": Path("reports/research_decisions/label_failure_analysis_v9_11.json"),
}

INPUT_PATHS = {
    "v9_38_validation": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "v9_38_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_validation_v9_38_manifest.json"),
    "v9_37_feature_store": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    "v9_37_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_37_manifest.json"),
    "v9_36_ohlcv_validation": Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json"),
    "v9_32_aggtrades_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

ALLOWED_DECISIONS = {
    "ohlcv_aggtrades_5y_dataset_created",
    "ohlcv_aggtrades_5y_dataset_created_with_warnings",
    "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels",
    "ohlcv_aggtrades_5y_dataset_blocked_by_label_quality",
    "ohlcv_aggtrades_5y_dataset_blocked_by_feature_quality",
    "ohlcv_aggtrades_5y_dataset_blocked_by_leakage",
    "ohlcv_aggtrades_5y_dataset_partial",
    "stop_ohlcv_aggtrades_5y_dataset_branch",
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
    "no_dataset_supervised": True,
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
