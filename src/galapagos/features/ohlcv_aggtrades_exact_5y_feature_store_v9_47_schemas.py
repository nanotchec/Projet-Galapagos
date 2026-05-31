from __future__ import annotations

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import FEATURE_COLUMNS as EXACT_FEATURE_COLUMNS
from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import EXPECTED_ROWS_BY_TIMEFRAME, EXPECTED_TIMEFRAMES, TARGET_WINDOW_END, TARGET_WINDOW_START
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_schemas import FEATURE_COLUMNS as BASE_FEATURE_COLUMNS


EXPECTED_DAYS = 1827
SOURCE = "binance_archive"
VENUE = "binance"
MARKET_TYPE = "spot"
SYMBOL = "BTCUSDT"
COMBINED_FEATURE_SCHEMA_VERSION = "ohlcv_aggtrades_exact_5y_features_v9_47_v1"
BASE_FEATURE_SCHEMA_VERSION = "ohlcv_aggtrades_5y_features_v9_37_v1"
EXACT_FEATURE_SCHEMA_VERSION = "aggtrades_exact_5y_features_v9_45_v1"

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
    "combined_feature_run_id",
    "combined_feature_schema_version",
    "base_feature_schema_version",
    "exact_feature_schema_version",
    "source_base_feature_store_version",
    "source_base_feature_validation_version",
    "source_exact_feature_store_version",
    "source_exact_feature_validation_version",
    "source_window_start",
    "source_window_end",
]

AUDIT_COLUMNS = [
    "warmup_row",
    "zero_trade_bucket",
    "feature_null_count",
    "feature_error_count",
    "combined_feature_null_count",
    "combined_feature_error_count",
    "row_valid_for_combined_features",
    "combined_feature_invalid_reason",
]

FEATURE_COLUMNS = list(BASE_FEATURE_COLUMNS) + list(EXACT_FEATURE_COLUMNS)
SOURCE_AUDIT_COLUMNS_INHERITED_AS_FEATURES = [
    "no_trade_bucket",
    "exact_feature_null_count",
    "exact_feature_error_count",
]
STRICT_COLUMNS = METADATA_COLUMNS + FEATURE_COLUMNS + AUDIT_COLUMNS

FEATURE_FAMILIES = {
    "base_v9_37": list(BASE_FEATURE_COLUMNS),
    "exact_aggtrades_v9_45": list(EXACT_FEATURE_COLUMNS),
}

FORBIDDEN_FEATURE_COLUMNS = {
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
    "label",
    "target",
    "future",
}
