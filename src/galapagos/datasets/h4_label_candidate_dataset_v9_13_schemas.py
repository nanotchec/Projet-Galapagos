from __future__ import annotations

from pathlib import Path

from galapagos.features.refined_ohlcv_trades_schemas import REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0
from galapagos.labels.horizon_event_label_redesign_v9_12_schemas import (
    HORIZON_EVENT_LABEL_COLUMNS_V9_12,
    WINDOW_END_V9_12,
    WINDOW_START_V9_12,
)


VERSION_V9_13_DATASET = "V9.13"
DATASET_SCHEMA_VERSION_V9_13 = "H4_LABEL_CANDIDATE_DATASET_COLUMNS_V9_13"
TIMEFRAMES_V9_13 = ["1m", "5m", "15m", "1h"]
WINDOW_START_V9_13 = WINDOW_START_V9_12
WINDOW_END_V9_13 = WINDOW_END_V9_12
TOTAL_DAYS_V9_13 = 366
EXPECTED_ROWS_V9_13 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}
TARGET_NAME_V9_13 = "up_down_flat_volnorm_h4"

INPUT_FEATURE_MANIFEST_V9_0 = Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json")
INPUT_LABEL_MANIFEST_V9_12 = Path("reports/manifests/horizon_event_label_redesign_v9_12_manifest.json")
INPUT_LABEL_REPORT_V9_12 = Path("reports/labels/horizon_event_label_redesign_v9_12.json")

MANIFEST_PATH_DATASET_V9_13 = Path("reports/manifests/h4_label_candidate_dataset_v9_13_manifest.json")
REPORT_JSON_PATH_DATASET_V9_13 = Path("reports/datasets/h4_label_candidate_dataset_v9_13.json")
REPORT_MD_PATH_DATASET_V9_13 = Path("reports/datasets/h4_label_candidate_dataset_v9_13.md")
DATACARD_MD_PATH_DATASET_V9_13 = Path("reports/datasets/h4_label_candidate_dataset_v9_13_datacard.md")
DOC_PATH_DATASET_V9_13 = Path("docs/h4_label_candidate_dataset_v9_13.md")

JOIN_KEYS_V9_13 = ["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts"]
FEATURE_COLUMNS_V9_13 = [
    *REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0,
    "warmup_row",
    "refined_feature_null_count",
    "refined_feature_error_count",
]
ML_FEATURE_COLUMNS_V9_13 = list(REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0)
LABEL_COLUMNS_V9_13 = [
    column
    for column in HORIZON_EVENT_LABEL_COLUMNS_V9_12
    if column
    not in {
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "close_ts",
        "decision_ts",
        "label_available_ts",
        "warmup_row",
    }
]
DATASET_COLUMNS_V9_13 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "available_ts",
    "decision_ts",
    "feature_available_ts",
    "label_available_ts",
    "dataset_run_id",
    "dataset_schema_version",
    "source_features_path",
    "source_labels_path",
    *FEATURE_COLUMNS_V9_13,
    *LABEL_COLUMNS_V9_13,
    "split",
    "split_order",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
]
SPLIT_COLUMNS_V9_13 = [*JOIN_KEYS_V9_13, "split", "split_order", "walk_forward_group"]
SPLIT_POLICY_V9_13 = {
    "train_ratio": 0.60,
    "validation_ratio": 0.20,
    "test_ratio": 0.20,
    "shuffle": False,
    "walk_forward_group": "calendar_month",
}

FORBIDDEN_DATASET_COLUMNS_V9_13 = {
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
    "trade",
}

ALLOWED_DATASET_DECISIONS_V9_13 = {
    "dataset_created_h4_label_candidate",
    "dataset_not_ready_missing_full_data",
    "dataset_not_ready_alignment_failed",
    "dataset_created_but_requires_review",
    "stop_h4_candidate_dataset_failed",
}

SAFETY_FLAGS_DATASET_V9_13 = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "ml_enabled": False,
    "labels_enabled": True,
    "dataset_enabled": True,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
    "persistent_model_created": False,
    "sidecars_created": False,
    "zip_fingerprints_created": False,
}

FINDINGS_V9_13 = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

EXPECTED_DATASET_LIMITATIONS_V9_13 = [
    "V9.13 assemble uniquement un dataset supervise offline avec le label candidat h4 V9.12.",
    "V9.13 dataset ne produit aucun score ML, aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
]


def get_h4_candidate_dataset_path_v9_13(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_13/datasets/h4_label_candidate"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_13}_{WINDOW_END_V9_13}"
        / "dataset.parquet"
    )


def get_h4_candidate_split_path_v9_13(root: Path, timeframe: str) -> Path:
    return get_h4_candidate_dataset_path_v9_13(root, timeframe).with_name("splits.parquet")
