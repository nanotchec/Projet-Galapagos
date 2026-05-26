from __future__ import annotations

from pathlib import Path

from galapagos.features.ohlcv_trades_1y_schemas import (
    OHLCV_TRADES_FEATURE_FAMILIES_V8_3,
    OHLCV_TRADES_FEATURE_COLUMNS_V8_3,
)
from galapagos.ml.schemas import ALLOWED_FEATURE_COLUMNS_V8_7, TIMEFRAMES_V8_7


VERSION_V8_9 = "V8.9"
TIMEFRAMES_V8_9 = TIMEFRAMES_V8_7.copy()

MANIFEST_PATH_V8_9 = Path("reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json")
REPORT_JSON_PATH_V8_9 = Path("reports/features/ohlcv_trades_feature_audit_v8_9.json")
REPORT_MD_PATH_V8_9 = Path("reports/features/ohlcv_trades_feature_audit_v8_9.md")
SELECTION_JSON_PATH_V8_9 = Path("reports/features/ohlcv_trades_feature_selection_v8_9.json")
SELECTION_MD_PATH_V8_9 = Path("reports/features/ohlcv_trades_feature_selection_v8_9.md")
DOC_PATH_V8_9 = Path("docs/ohlcv_trades_feature_audit_v8_9.md")

AUDIT_DIR_V8_9 = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON_V8_9 = AUDIT_DIR_V8_9 / "v8_9_artifact_inventory.json"
ARTIFACT_INVENTORY_MD_V8_9 = AUDIT_DIR_V8_9 / "v8_9_artifact_inventory.md"
ATTESTATION_JSON_V8_9 = AUDIT_DIR_V8_9 / "v8_9_full_local_validation_attestation.json"
ATTESTATION_MD_V8_9 = AUDIT_DIR_V8_9 / "v8_9_full_local_validation_attestation.md"
ZIP_SIZE_JSON_V8_9 = AUDIT_DIR_V8_9 / "zip_size_report_v8_9.json"
ZIP_SIZE_MD_V8_9 = AUDIT_DIR_V8_9 / "zip_size_report_v8_9.md"
ZIP_AUDIT_JSON_V8_9 = AUDIT_DIR_V8_9 / "zip_audit_v8_9.json"
ZIP_AUDIT_MD_V8_9 = AUDIT_DIR_V8_9 / "zip_audit_v8_9.md"
ZIP_SMOKE_JSON_V8_9 = AUDIT_DIR_V8_9 / "zip_smoke_v8_9.json"
ZIP_SMOKE_MD_V8_9 = AUDIT_DIR_V8_9 / "zip_smoke_v8_9.md"
COMMAND_TIMINGS_JSON_V8_9 = AUDIT_DIR_V8_9 / "v8_9_command_timings.json"
ZIP_NAME_V8_9 = "projet-galapagos-v8.9-audit-lite.zip"

INPUT_DATASET_MANIFEST_PATH_V8_9 = Path("reports/manifests/ohlcv_trades_1y_offline_supervised_dataset_v8_4_manifest.json")
INPUT_FEATURE_MANIFEST_PATH_V8_9 = Path("reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json")
INPUT_FEATURE_REPORT_PATH_V8_9 = Path("reports/features/ohlcv_trades_1y_feature_store_v8_3.json")
INPUT_ML_MANIFEST_PATH_V8_9 = Path("reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json")
INPUT_ML_REPORT_PATH_V8_9 = Path("reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.json")
INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9 = Path("reports/manifests/strict_walk_forward_validation_v8_7_manifest.json")
INPUT_WALK_FORWARD_REPORT_PATH_V8_9 = Path("reports/ml/strict_walk_forward_validation_v8_7.json")
INPUT_DECISION_JSON_PATH_V8_9 = Path("reports/research_decisions/v8_8_research_decision_gate.json")
INPUT_DECISION_MD_PATH_V8_9 = Path("reports/research_decisions/v8_8_research_decision_gate.md")

ALLOWED_FEATURE_COLUMNS_V8_9 = ALLOWED_FEATURE_COLUMNS_V8_7.copy()
ORIGINAL_FEATURE_COLUMNS_COUNT_V8_9 = len(ALLOWED_FEATURE_COLUMNS_V8_9)
ALL_V8_3_DATASET_FEATURE_COLUMNS_V8_9 = OHLCV_TRADES_FEATURE_COLUMNS_V8_3[15:]
AUDIT_ONLY_COLUMNS_V8_9 = ["warmup_row", "trades_feature_null_count", "trades_feature_error_count"]
REQUIRED_CORE_FEATURES_V8_9 = [
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
    "taker_buy_ratio_quantity",
    "taker_imbalance_quantity",
    "agg_trades_per_minute",
    "trade_flow_pressure",
    "hour_utc",
    "day_of_week_utc",
    "is_weekend_utc",
]

FEATURE_FAMILY_ALIASES_V8_9 = {
    "ohlcv_base_reference": "ohlcv_base",
    "trade_aggregation": "trade_aggregation",
    "aggressor_taker_approximation": "taker_flow",
    "trade_intensity": "trade_intensity",
    "rolling_trade_features": "rolling_trade",
    "microstructure_proxies": "microstructure_proxy",
    "temporal": "temporal",
    "audit": "audit",
}

FEATURE_FAMILY_BY_COLUMN_V8_9: dict[str, str] = {}
for raw_family, columns in OHLCV_TRADES_FEATURE_FAMILIES_V8_3.items():
    family = FEATURE_FAMILY_ALIASES_V8_9[raw_family]
    for column in columns:
        FEATURE_FAMILY_BY_COLUMN_V8_9[column] = family

FEATURE_FAMILIES_V8_9 = [
    "ohlcv_base",
    "trade_aggregation",
    "taker_flow",
    "trade_intensity",
    "rolling_trade",
    "microstructure_proxy",
    "temporal",
    "audit",
]

SOURCE_TYPES_V8_9 = {
    "ohlcv_base": "ohlcv_base",
    "trade_aggregation": "trade_aggregation",
    "taker_flow": "taker_flow",
    "trade_intensity": "trade_intensity",
    "rolling_trade": "rolling_trade",
    "microstructure_proxy": "microstructure_proxy",
    "temporal": "temporal",
    "audit": "audit",
}

FORBIDDEN_FEATURE_PREFIXES_V8_9 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]

FORBIDDEN_FEATURE_EXACT_V8_9 = [
    "target",
    "split",
    "walk_forward_group",
    "fold_id",
    "fold_role",
    "fold_order",
    "is_embargoed",
    "is_purged",
    "prediction",
    "predicted",
    "signal",
    "trading_signal",
    "strategy",
    "order",
    "pnl",
    "profit",
    "backtest",
    "position_size",
    "trade_decision",
    "execution",
    "paper_live",
]

FORBIDDEN_MARKDOWN_CLAIMS_V8_9 = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "model validated for trading",
    "features validated for trading",
]

SAFETY_FLAGS_V8_9 = {
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

EXPECTED_LIMITATIONS_V8_9 = [
    "V8.9 audite et propose uniquement une selection/refactorisation de features OHLCV + aggTrades.",
    "V8.9 ne produit aucun nouveau dataset, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
    "La selection proposee doit etre revalidee dans V9.0/V9.x avant toute interpretation.",
]

FINDINGS_FALSE_FIELDS_V8_9 = [
    "feature_set_validated_for_trading",
    "strategy_validated",
    "backtest_performed",
    "actionable_signal_produced",
]

COLLINEARITY_SAMPLE_SEED_V8_9 = 8900
COLLINEARITY_SAMPLE_ROWS_PER_TIMEFRAME_V8_9 = 5000
COLLINEARITY_THRESHOLD_V8_9 = 0.95
