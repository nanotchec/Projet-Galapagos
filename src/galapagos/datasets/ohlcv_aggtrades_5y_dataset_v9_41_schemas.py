from __future__ import annotations

from pathlib import Path


VERSION = "V9.41"
SOURCE_VERSION = "V9.40"
LAST_VALIDATED_VERSION = "V9.40"
DIRECTION = "ohlcv_aggtrades_5y_dataset"

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

SOURCE_FEATURE_STORE_VERSION = "V9.37"
SOURCE_FEATURE_VALIDATION_VERSION = "V9.38"
SOURCE_LABEL_VERSION = "V9.40"
DATASET_SCHEMA_VERSION = "OHLCV_AGGTRADES_5Y_DATASET_V9_41"
DATASET_RUN_ID_PREFIX = "v9_41"
SELECTED_PRIMARY_LABEL = "up_down_flat_volnorm_h1_5y"
DIAGNOSTIC_LABELS = ("up_down_flat_volnorm_h4_5y", "binary_directional_volnorm_h4_5y")
LABEL_COLUMNS = (SELECTED_PRIMARY_LABEL, *DIAGNOSTIC_LABELS, "label_valid", "label_invalid_reason")

FEATURE_BASE_PATH = Path("data/research/v9_37/features/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
LABEL_BASE_PATH = Path("data/research/v9_40/labels/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
DATASET_BASE_PATH = Path("data/research/v9_41/datasets/ohlcv_aggtrades_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")

REPORT_JSON_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json")
REPORT_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.md")
DATACARD_MD_PATH = Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41_datacard.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_dataset_v9_41_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_dataset_v9_41.md")

INPUT_PATHS = {
    "v9_40_label_factory": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
    "v9_40_label_factory_md": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.md"),
    "v9_40_label_datacard": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40_datacard.md"),
    "v9_40_label_distribution": Path("reports/labels/ohlcv_aggtrades_5y_label_distribution_v9_40.json"),
    "v9_40_label_stability": Path("reports/labels/ohlcv_aggtrades_5y_label_stability_v9_40.json"),
    "v9_40_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_label_factory_v9_40_manifest.json"),
    "v9_38_feature_validation": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "v9_37_feature_store": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    "v9_38_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_validation_v9_38_manifest.json"),
    "v9_37_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_37_manifest.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

SPLIT_POLICY = {
    "shuffle": False,
    "train_ratio": 0.60,
    "validation_ratio": 0.20,
    "test_ratio": 0.20,
    "walk_forward_group": "calendar_month",
    "purge_embargo_group": "none_v9_41_preview",
}

FEATURE_COLUMNS = [
    "close_return_1",
    "log_return_1",
    "rolling_return_5",
    "rolling_return_15",
    "rolling_return_60",
    "rolling_volatility_5",
    "rolling_volatility_15",
    "rolling_volatility_60",
    "high_low_range",
    "close_open_return",
    "candle_body",
    "upper_wick",
    "lower_wick",
    "volume",
    "quote_volume",
    "trades_count",
    "volume_rolling_mean_5",
    "volume_rolling_mean_15",
    "volume_rolling_mean_60",
    "volume_rolling_std_5",
    "volume_rolling_std_15",
    "volume_rolling_std_60",
    "zero_trade_bucket_rolling_count_60",
    "agg_trade_count",
    "agg_trade_volume",
    "agg_trade_quote_volume",
    "average_trade_size",
    "taker_buy_base_volume",
    "taker_sell_base_volume",
    "taker_buy_ratio",
    "taker_buy_sell_imbalance",
    "trade_intensity_rolling_5",
    "trade_intensity_rolling_15",
    "trade_intensity_rolling_60",
    "agg_trade_volume_rolling_mean_5",
    "agg_trade_volume_rolling_mean_15",
    "agg_trade_volume_rolling_mean_60",
    "taker_imbalance_rolling_mean_5",
    "taker_imbalance_rolling_mean_15",
    "taker_imbalance_rolling_mean_60",
    "missing_aggtrades_flag",
]

FEATURE_AUDIT_COLUMNS = [
    "warmup_row",
    "zero_trade_bucket",
    "feature_null_count",
    "feature_error_count",
    "row_valid_for_features",
    "feature_invalid_reason",
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
    "feature_schema_version",
    "label_schema_version",
    "source_feature_store_version",
    "source_feature_validation_version",
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
    "ohlcv_aggtrades_5y_dataset_created",
    "ohlcv_aggtrades_5y_dataset_created_with_warnings",
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
