from __future__ import annotations

from pathlib import Path


VERSION = "V9.64"
SOURCE_VERSION = "V9.63"
DIRECTION = "redesigned_5y_label_factory"
TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
WINDOW_LABEL = "2021-05-05_2026-05-05"
TIMEFRAMES = ("1m", "5m", "15m", "1h")
TIMEFRAME_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
LABEL_SCHEMA_VERSION = "REDESIGNED_5Y_LABELS_V9_64"
LABEL_RUN_ID_PREFIX = "v9_64"
SELECTED_PRIMARY_LABEL = "binary_directional_volnorm_h4_5y"

SOURCE_FEATURE_STORE_VERSION = "V9.47"
SOURCE_LABEL_DIAGNOSTIC_VERSION = "V9.63"

FEATURE_BASE_PATH = Path("data/research/v9_47/features/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
LABEL_BASE_PATH = Path("data/research/v9_64/labels/redesigned_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")

REPORT_JSON_PATH = Path("reports/labels/redesigned_5y_label_factory_v9_64.json")
REPORT_MD_PATH = Path("reports/labels/redesigned_5y_label_factory_v9_64.md")
DISTRIBUTION_JSON_PATH = Path("reports/labels/redesigned_5y_label_distribution_v9_64.json")
MANIFEST_PATH = Path("reports/manifests/redesigned_5y_label_factory_v9_64_manifest.json")
DOC_PATH = Path("docs/redesigned_5y_label_factory_v9_64.md")

INPUT_PATHS = {
    "v9_63_diagnostic": Path("reports/research_decisions/label_redesign_diagnostic_v9_63.json"),
    "v9_47_feature_store": Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.json"),
    "v9_48_to_v9_51_protocol": Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
}

LABEL_DESIGNS = {
    "binary_directional_volnorm_h1_5y": {"horizon_minutes": 60, "mode": "binary_volnorm", "threshold_multiplier": 0.10},
    "binary_directional_volnorm_h4_5y": {"horizon_minutes": 240, "mode": "binary_volnorm", "threshold_multiplier": 0.10},
    "quantile_directional_h1_5y": {"horizon_minutes": 60, "mode": "binary_quantile_train_median"},
    "quantile_directional_h4_5y": {"horizon_minutes": 240, "mode": "binary_quantile_train_median"},
    "up_down_flat_quantile_h1_5y": {"horizon_minutes": 60, "mode": "ternary_quantile_train_thirds"},
}

LABEL_COLUMNS = tuple(LABEL_DESIGNS)

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
    "source_label_diagnostic_version",
    "selected_primary_label",
    "target_name",
    "horizon_name",
    "horizon_minutes",
    "future_log_return_h1",
    "future_log_return_h4",
    "causal_vol_window_bars",
    "causal_realized_vol",
    "volatility_threshold_multiplier_h1",
    "volatility_threshold_multiplier_h4",
    "volatility_normalized_threshold_h1",
    "volatility_normalized_threshold_h4",
    "train_quantile_median_h1",
    "train_quantile_median_h4",
    "train_quantile_lower_h1",
    "train_quantile_upper_h1",
    *LABEL_COLUMNS,
    "label_valid",
    "label_invalid_reason",
    "warmup_row",
    "label_null_count",
    "label_error_count",
]

ALLOWED_DECISIONS = {
    "redesigned_labels_created",
    "redesigned_labels_created_with_warnings",
    "redesigned_labels_blocked_by_quality",
    "redesigned_labels_blocked_by_leakage",
    "redesigned_labels_manual_review_required",
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
