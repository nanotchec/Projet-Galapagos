from __future__ import annotations

from pathlib import Path

from galapagos.features.funding_only_feature_store_v9_57_schemas import FEATURE_COLUMNS as FUNDING_FEATURE_COLUMNS
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import FEATURE_COLUMNS as BASE_FEATURE_COLUMNS


VERSION = "V9.59"
SOURCE_VERSION = "V9.56_to_V9.58"
DIRECTION = "ohlcv_aggtrades_exact_funding_5y_common_window_feature_store"

SOURCE = "binance_archive"
VENUE = "binance"
MARKET_TYPE = "mixed_spot_futures_um"
SYMBOL = "BTCUSDT"
TIMEFRAMES = ("1m", "5m", "15m", "1h")
COMMON_WINDOW_START = "2021-05-05T00:00:00Z"
COMMON_WINDOW_END = "2026-04-30T16:00:00Z"
COMMON_WINDOW_LABEL = "2021-05-05_to_2026-04-30T16-00-00Z"
COMMON_WINDOW_POLICY = "closed_exact_at_last_known_funding_timestamp_no_imputation_no_tail_forward_fill"

BASE_FEATURE_STORE_VERSION = "V9.47"
BASE_FEATURE_VALIDATION_VERSION = "V9.48"
FUNDING_FEATURE_STORE_VERSION = "V9.57"
FUNDING_FEATURE_VALIDATION_VERSION = "V9.58"
FEATURE_SCHEMA_VERSION = "ohlcv_aggtrades_exact_funding_5y_common_window_features_v9_59_v1"
FEATURE_RUN_ID_PREFIX = "v9_59"

BASE_FEATURE_ROOT = Path("data/research/v9_47/features/ohlcv_aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT")
FUNDING_FEATURE_ROOT = Path("data/research/v9_57/features/funding_only/source=binance_archive/market_type=futures_um/symbol=BTCUSDT")
OUTPUT_ROOT = Path("data/research/v9_59/features/ohlcv_aggtrades_exact_funding_5y_common_window/source=binance_archive/market_type=mixed_spot_futures_um/symbol=BTCUSDT")

REPORT_JSON_PATH = Path("reports/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.json")
REPORT_MD_PATH = Path("reports/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.md")

INPUT_PATHS = {
    "funding_chain": Path("reports/research_decisions/funding_tail_and_feature_chain_v9_56_to_v9_58.json"),
    "funding_validation": Path("reports/features/funding_only_feature_store_validation_v9_58.json"),
    "funding_store": Path("reports/features/funding_only_feature_store_v9_57.json"),
    "base_validation": Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json"),
    "base_store": Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.json"),
}

METADATA_COLUMNS = [
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
    "funding_common_feature_run_id",
    "funding_common_feature_schema_version",
    "source_base_feature_store_version",
    "source_base_feature_validation_version",
    "source_funding_feature_store_version",
    "source_funding_feature_validation_version",
    "source_window_start",
    "source_window_end",
    "actual_window_start",
    "actual_window_end",
    "common_window_policy",
]

FEATURE_COLUMNS = list(BASE_FEATURE_COLUMNS) + list(FUNDING_FEATURE_COLUMNS)

BASE_AUDIT_COLUMNS = [
    "warmup_row",
    "zero_trade_bucket",
    "feature_null_count",
    "feature_error_count",
    "combined_feature_null_count",
    "combined_feature_error_count",
    "row_valid_for_combined_features",
    "combined_feature_invalid_reason",
]
FUNDING_AUDIT_COLUMNS = [
    "row_valid_for_funding_features",
    "funding_feature_null_count",
    "funding_feature_error_count",
    "funding_feature_invalid_reason",
]
AUDIT_COLUMNS = [
    *BASE_AUDIT_COLUMNS,
    *FUNDING_AUDIT_COLUMNS,
    "row_valid_for_funding_common_features",
    "funding_common_feature_null_count",
    "funding_common_feature_error_count",
    "funding_common_feature_invalid_reason",
]

STRICT_COLUMNS = METADATA_COLUMNS + FEATURE_COLUMNS + AUDIT_COLUMNS

FORBIDDEN_FEATURE_TOKENS = {
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
    "label",
    "target",
    "future_return",
    "next_return",
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
