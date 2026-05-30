from __future__ import annotations

from pathlib import Path


VERSION = "V9.40"
SOURCE_VERSION = "V9.39"
LAST_VALIDATED_VERSION = "V9.39"
DIRECTION = "ohlcv_aggtrades_5y_label_factory"

TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
TOTAL_DAYS = 1827
TIMEFRAMES = ("1m", "5m", "15m", "1h")
TIMEFRAME_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
EXPECTED_FEATURE_ROWS = {
    "1m": 2_630_880,
    "5m": 526_176,
    "15m": 175_392,
    "1h": 43_848,
}

SOURCE_FEATURE_STORE_VERSION = "V9.37"
SOURCE_FEATURE_VALIDATION_VERSION = "V9.38"
SOURCE_OHLCV_VERSION = "V9.36"
LABEL_SCHEMA_VERSION = "OHLCV_AGGTRADES_5Y_LABELS_V9_40"
LABEL_RUN_ID_PREFIX = "v9_40"
SELECTED_PRIMARY_LABEL = "up_down_flat_volnorm_h4_5y"

FEATURE_BASE_PATH = Path("data/research/v9_37/features/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
LABEL_BASE_PATH = Path("data/research/v9_40/labels/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")

REPORT_JSON_PATH = Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json")
REPORT_MD_PATH = Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.md")
DATACARD_MD_PATH = Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40_datacard.md")
DISTRIBUTION_JSON_PATH = Path("reports/labels/ohlcv_aggtrades_5y_label_distribution_v9_40.json")
STABILITY_JSON_PATH = Path("reports/labels/ohlcv_aggtrades_5y_label_stability_v9_40.json")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_label_factory_v9_40_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_label_factory_v9_40.md")

INPUT_PATHS = {
    "v9_39_dataset_readiness": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_39.json"),
    "v9_39_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_dataset_v9_39_manifest.json"),
    "v9_38_feature_validation": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "v9_37_feature_store": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    "v9_36_ohlcv_validation": Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json"),
    "v9_11_label_failure": Path("reports/research_decisions/label_failure_analysis_v9_11.json"),
    "v9_12_label_redesign": Path("reports/labels/horizon_event_label_redesign_v9_12.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

LABEL_DESIGNS = {
    "up_down_flat_volnorm_h4_5y": {
        "horizon_name": "h4",
        "horizon_minutes": 240,
        "threshold_multiplier": 1.25,
        "mode": "ternary_volnorm",
        "role": "primary_candidate",
    },
    "up_down_flat_volnorm_h1_5y": {
        "horizon_name": "h1",
        "horizon_minutes": 60,
        "threshold_multiplier": 0.75,
        "mode": "ternary_volnorm",
        "role": "diagnostic_candidate",
    },
    "binary_directional_volnorm_h4_5y": {
        "horizon_name": "h4",
        "horizon_minutes": 240,
        "threshold_multiplier": 0.0,
        "mode": "binary_directional",
        "role": "diagnostic_candidate",
    },
}

REQUIRED_LABEL_COLUMNS = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "label_start_ts",
    "label_end_ts",
    "label_available_ts",
    "label_run_id",
    "label_schema_version",
    "source_feature_store_version",
    "source_ohlcv_version",
    "target_name",
    "horizon_name",
    "horizon_minutes",
    "future_log_return",
    "causal_vol_window_bars",
    "causal_vol_min_periods",
    "causal_realized_vol",
    "volatility_threshold_multiplier",
    "volatility_normalized_threshold",
    "up_down_flat_volnorm_h4_5y",
    "up_down_flat_volnorm_h1_5y",
    "binary_directional_volnorm_h4_5y",
    "label_valid",
    "label_invalid_reason",
    "warmup_row",
    "label_null_count",
    "label_error_count",
]

FORBIDDEN_LABEL_COLUMNS = {
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
    "ohlcv_aggtrades_5y_labels_created",
    "ohlcv_aggtrades_5y_labels_created_with_warnings",
    "ohlcv_aggtrades_5y_labels_blocked_by_quality",
    "ohlcv_aggtrades_5y_labels_blocked_by_leakage",
    "ohlcv_aggtrades_5y_labels_partial",
    "ohlcv_aggtrades_5y_labels_requires_manual_review",
    "stop_5y_label_branch",
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
