from __future__ import annotations

from pathlib import Path

from galapagos.features.schemas import FEATURE_COLUMNS_V2_5
from galapagos.labels.schemas import LABEL_COLUMNS_V2_6

VERSION = "V2.7"
DATASET_SCHEMA_VERSION = "V2.7"
TARGET_TIMEFRAMES = ["1m", "5m", "15m", "1h"]
EXPECTED_ROWS_BY_TIMEFRAME = {"1m": 1440, "5m": 288, "15m": 96, "1h": 24}

MANIFEST_PATH = Path("reports/manifests/offline_supervised_dataset_v2_7_manifest.json")
REPORT_JSON_PATH = Path("reports/datasets/offline_supervised_dataset_v2_7.json")
REPORT_MD_PATH = Path("reports/datasets/offline_supervised_dataset_v2_7.md")
DATACARD_MD_PATH = Path("reports/datasets/offline_supervised_dataset_v2_7_datacard.md")

JOIN_KEYS = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "available_ts",
    "decision_ts",
]

FEATURE_VALUE_COLUMNS = [
    "close_lag_1",
    "return_1",
    "log_return_1",
    "return_3",
    "log_return_3",
    "return_5",
    "log_return_5",
    "rolling_vol_5",
    "rolling_vol_15",
    "rolling_vol_30",
    "candle_range",
    "candle_body",
    "upper_wick",
    "lower_wick",
    "close_position_in_range",
    "volume_lag_1",
    "volume_return_1",
    "rolling_volume_mean_5",
    "rolling_volume_mean_15",
    "rolling_volume_zscore_15",
    "sma_5",
    "sma_15",
    "sma_30",
    "close_to_sma_5",
    "close_to_sma_15",
    "close_to_sma_30",
    "hour_utc",
    "day_of_week_utc",
    "is_weekend_utc",
    "warmup_row",
    "feature_null_count",
    "feature_error_count",
]

LABEL_VALUE_COLUMNS = [
    "future_close_h1",
    "future_log_return_h1",
    "future_simple_return_h1",
    "direction_h1",
    "up_down_flat_h1",
    "label_end_ts_h1",
    "label_valid_h1",
    "future_close_h3",
    "future_log_return_h3",
    "future_simple_return_h3",
    "direction_h3",
    "up_down_flat_h3",
    "label_end_ts_h3",
    "label_valid_h3",
    "future_close_h5",
    "future_log_return_h5",
    "future_simple_return_h5",
    "direction_h5",
    "up_down_flat_h5",
    "label_end_ts_h5",
    "label_valid_h5",
    "label_null_count",
    "label_error_count",
    "tail_row",
]

DATASET_COLUMNS_V2_7 = [
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
    *FEATURE_VALUE_COLUMNS,
    *LABEL_VALUE_COLUMNS,
    "split",
    "split_order",
    "purge_embargo_group",
    "dataset_null_count",
    "dataset_error_count",
]

SPLIT_COLUMNS_V2_7 = [*JOIN_KEYS, "split", "split_order", "purge_embargo_group"]

FORBIDDEN_DATASET_COLUMN_TERMS = [
    "prediction",
    "predicted",
    "model_score",
    "score_ml",
    "alpha",
    "signal",
    "strategy",
    "order",
    "trade_decision",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
    "live",
    "paper_live",
]

EXPECTED_LIMITATIONS_V2_7 = [
    "V2.7 assemble uniquement un dataset supervise offline a partir des features V2.5 et labels V2.6 valides sur BTCUSDT 2024-01-15.",
    "V2.7 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]

SPLIT_POLICY_V2_7 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v2_7_preview",
}

VERSION_V3_2 = "V3.2"
DATASET_SCHEMA_VERSION_V3_2 = "V3.2"
TIMEFRAMES_V3_2 = ["1m", "5m", "15m", "1h"]
EXPECTED_ROWS_V3_2 = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}
EXPECTED_SPLIT_COUNTS_V3_2 = {
    "1m": {"train": 6048, "validation": 2016, "test": 2016},
    "5m": {"train": 1209, "validation": 403, "test": 404},
    "15m": {"train": 403, "validation": 134, "test": 135},
    "1h": {"train": 100, "validation": 33, "test": 35},
}

MANIFEST_PATH_V3_2 = Path("reports/manifests/multi_day_offline_supervised_dataset_v3_2_manifest.json")
REPORT_JSON_PATH_V3_2 = Path("reports/datasets/multi_day_offline_supervised_dataset_v3_2.json")
REPORT_MD_PATH_V3_2 = Path("reports/datasets/multi_day_offline_supervised_dataset_v3_2.md")
DATACARD_MD_PATH_V3_2 = Path("reports/datasets/multi_day_offline_supervised_dataset_v3_2_datacard.md")
DOC_PATH_V3_2 = Path("docs/multi_day_offline_supervised_dataset_v3_2.md")

DATASET_COLUMNS_V3_2 = [
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
    *FEATURE_VALUE_COLUMNS,
    *LABEL_VALUE_COLUMNS,
    "split",
    "split_order",
    "purge_embargo_group",
    "dataset_null_count",
    "dataset_error_count",
]

SPLIT_COLUMNS_V3_2 = [*JOIN_KEYS, "split", "split_order", "purge_embargo_group"]

SPLIT_POLICY_V3_2 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v3_2_preview",
}

EXPECTED_LIMITATIONS_V3_2 = [
    "V3.2 assemble uniquement un dataset supervise offline multi-day a partir des features V3.0 et labels V3.1 valides sur BTCUSDT 2024-01-15 a 2024-01-21.",
    "V3.2 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def get_dataset_gold_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/gold/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "year=2024"
        / "month=01"
        / "dataset-2024-01-15.parquet"
    )


def get_split_gold_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/gold/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "year=2024"
        / "month=01"
        / "splits-2024-01-15.parquet"
    )


def get_dataset_v3_2_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_2/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "window=2024-01-15_2024-01-21"
        / "dataset.parquet"
    )


def get_split_v3_2_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_2/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "window=2024-01-15_2024-01-21"
        / "splits.parquet"
    )


def assert_source_schema_imports() -> None:
    missing_features = [column for column in FEATURE_VALUE_COLUMNS if column not in FEATURE_COLUMNS_V2_5]
    missing_labels = [column for column in LABEL_VALUE_COLUMNS if column not in LABEL_COLUMNS_V2_6]
    if missing_features or missing_labels:
        raise RuntimeError(
            f"V2.7 source schema mismatch: missing_features={missing_features}, missing_labels={missing_labels}"
        )
