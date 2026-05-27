from __future__ import annotations

from pathlib import Path

from galapagos.features.refined_ohlcv_trades_schemas import REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0
from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import (
    REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
    WINDOW_END_V9_6,
    WINDOW_START_V9_6,
)


VERSION_V9_7 = "V9.7"
DATASET_SCHEMA_VERSION_V9_7 = "DATASET_COLUMNS_V9_7"
TIMEFRAMES_V9_7 = ["1m", "5m", "15m", "1h"]
WINDOW_START_V9_7 = WINDOW_START_V9_6
WINDOW_END_V9_7 = WINDOW_END_V9_6
TOTAL_DAYS_V9_7 = 366
EXPECTED_ROWS_V9_7 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}
TARGET_NAME_V9_7 = "up_down_flat_volnorm_h1"

MANIFEST_PATH_V9_7 = Path("reports/manifests/refined_volnorm_labels_dataset_v9_7_manifest.json")
REPORT_JSON_PATH_V9_7 = Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.json")
REPORT_MD_PATH_V9_7 = Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.md")
DATACARD_MD_PATH_V9_7 = Path("reports/datasets/refined_volnorm_labels_dataset_v9_7_datacard.md")
DOC_PATH_V9_7 = Path("docs/refined_volnorm_labels_dataset_v9_7.md")

JOIN_KEYS_V9_7 = ["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts"]
FEATURE_COLUMNS_V9_7 = [
    *REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0,
    "warmup_row",
    "refined_feature_null_count",
    "refined_feature_error_count",
]
LABEL_COLUMNS_V9_7 = [
    column
    for column in REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6
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
DATASET_COLUMNS_V9_7 = [
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
    "source_features_sha256",
    "source_labels_sha256",
    *FEATURE_COLUMNS_V9_7,
    *LABEL_COLUMNS_V9_7,
    "split",
    "split_order",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
]
SPLIT_COLUMNS_V9_7 = [*JOIN_KEYS_V9_7, "split", "split_order", "walk_forward_group"]
SPLIT_POLICY_V9_7 = {
    "train_ratio": 0.60,
    "validation_ratio": 0.20,
    "test_ratio": 0.20,
    "shuffle": False,
    "walk_forward_group": "calendar_month",
}

FORBIDDEN_DATASET_COLUMNS_V9_7 = {
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
}

ALLOWED_DECISIONS_V9_7 = {
    "dataset_created_with_volnorm_labels",
    "dataset_not_ready_missing_full_data",
    "dataset_not_ready_alignment_failed",
    "dataset_created_but_requires_review",
    "stop_refined_branch_dataset_failed",
}

SAFETY_FLAGS_V9_7 = {
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
}

EXPECTED_LIMITATIONS_V9_7 = [
    "V9.7 assemble uniquement un dataset supervise offline avec features raffinees V9.0 et labels volatility-normalized V9.6.",
    "V9.7 ne produit aucun modele ML, aucun score ML, aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
]


def get_refined_volnorm_dataset_path_v9_7(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_7/datasets/refined_volnorm_labels"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_7}_{WINDOW_END_V9_7}"
        / "dataset.parquet"
    )


def get_refined_volnorm_split_path_v9_7(root: Path, timeframe: str) -> Path:
    return get_refined_volnorm_dataset_path_v9_7(root, timeframe).with_name("splits.parquet")
