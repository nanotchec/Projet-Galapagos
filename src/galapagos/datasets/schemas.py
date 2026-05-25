from __future__ import annotations

from pathlib import Path

from galapagos.features.advanced_ohlcv_schemas import (
    ADVANCED_OHLCV_AUDIT_COLUMNS_V6_0,
    ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0,
)
from galapagos.features.ohlcv_trades_schemas import (
    OHLCV_TRADES_FEATURE_COLUMNS_V7_2,
    OHLCV_TRADES_METADATA_COLUMNS_V7_2,
)
from galapagos.features.ohlcv_trades_90d_schemas import (
    OHLCV_TRADES_FEATURE_COLUMNS_V7_8,
    OHLCV_TRADES_METADATA_COLUMNS_V7_8,
)
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


VERSION_V3_8 = "V3.8"
DATASET_SCHEMA_VERSION_V3_8 = "V3.8"
TIMEFRAMES_V3_8 = ["1m", "5m", "15m", "1h"]
WINDOW_V3_8 = "2024-01-01_2024-03-30"
EXPECTED_ROWS_V3_8 = {"1m": 129600, "5m": 25920, "15m": 8640, "1h": 2160}
EXPECTED_SPLIT_COUNTS_V3_8 = {
    "1m": {"train": 77760, "validation": 25920, "test": 25920},
    "5m": {"train": 15552, "validation": 5184, "test": 5184},
    "15m": {"train": 5184, "validation": 1728, "test": 1728},
    "1h": {"train": 1296, "validation": 432, "test": 432},
}

MANIFEST_PATH_V3_8 = Path("reports/manifests/expanded_offline_supervised_dataset_v3_8_manifest.json")
REPORT_JSON_PATH_V3_8 = Path("reports/datasets/expanded_offline_supervised_dataset_v3_8.json")
REPORT_MD_PATH_V3_8 = Path("reports/datasets/expanded_offline_supervised_dataset_v3_8.md")
DATACARD_MD_PATH_V3_8 = Path("reports/datasets/expanded_offline_supervised_dataset_v3_8_datacard.md")
DOC_PATH_V3_8 = Path("docs/expanded_offline_supervised_dataset_v3_8.md")

DATASET_COLUMNS_V3_8 = DATASET_COLUMNS_V3_2.copy()
SPLIT_COLUMNS_V3_8 = SPLIT_COLUMNS_V3_2.copy()

SPLIT_POLICY_V3_8 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v3_8_preview",
}

EXPECTED_LIMITATIONS_V3_8 = [
    "V3.8 assemble uniquement un dataset supervise offline 90 jours a partir des features V3.6 et labels V3.7 valides.",
    "V3.8 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]

VERSION_V4_5 = "V4.5"
DATASET_SCHEMA_VERSION_V4_5 = "V4.5"
TIMEFRAMES_V4_5 = ["1m", "5m", "15m", "1h"]
WINDOW_V4_5 = "2024-01-01_2024-12-31"
EXPECTED_ROWS_V4_5 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}
EXPECTED_SPLIT_COUNTS_V4_5 = {
    "1m": {"train": 316224, "validation": 105408, "test": 105408},
    "5m": {"train": 63244, "validation": 21082, "test": 21082},
    "15m": {"train": 21081, "validation": 7027, "test": 7028},
    "1h": {"train": 5270, "validation": 1757, "test": 1757},
}

MANIFEST_PATH_V4_5 = Path("reports/manifests/one_year_offline_supervised_dataset_v4_5_manifest.json")
REPORT_JSON_PATH_V4_5 = Path("reports/datasets/one_year_offline_supervised_dataset_v4_5.json")
REPORT_MD_PATH_V4_5 = Path("reports/datasets/one_year_offline_supervised_dataset_v4_5.md")
DATACARD_MD_PATH_V4_5 = Path("reports/datasets/one_year_offline_supervised_dataset_v4_5_datacard.md")
DOC_PATH_V4_5 = Path("docs/one_year_offline_supervised_dataset_v4_5.md")

DATASET_COLUMNS_V4_5 = DATASET_COLUMNS_V3_8.copy()
SPLIT_COLUMNS_V4_5 = SPLIT_COLUMNS_V3_8.copy()

SPLIT_POLICY_V4_5 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v4_5_preview",
}

EXPECTED_LIMITATIONS_V4_5 = [
    "V4.5 assemble uniquement un dataset supervise offline 1 an a partir des features V4.3 et labels V4.4 valides.",
    "V4.5 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]

VERSION_V5_3 = "V5.3"
DATASET_SCHEMA_VERSION_V5_3 = "V5.3"
TIMEFRAMES_V5_3 = ["1m", "5m", "15m", "1h"]

MANIFEST_PATH_V5_3 = Path("reports/manifests/max_history_offline_supervised_dataset_v5_3_manifest.json")
REPORT_JSON_PATH_V5_3 = Path("reports/datasets/max_history_offline_supervised_dataset_v5_3.json")
REPORT_MD_PATH_V5_3 = Path("reports/datasets/max_history_offline_supervised_dataset_v5_3.md")
DATACARD_MD_PATH_V5_3 = Path("reports/datasets/max_history_offline_supervised_dataset_v5_3_datacard.md")
DOC_PATH_V5_3 = Path("docs/max_history_offline_supervised_dataset_v5_3.md")

DATASET_COLUMNS_V5_3 = DATASET_COLUMNS_V4_5.copy()
SPLIT_COLUMNS_V5_3 = [*JOIN_KEYS, "split", "split_order", "purge_embargo_group", "walk_forward_group"]

SPLIT_POLICY_V5_3 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v5_3_preview",
    "walk_forward_grouping": "calendar_quarter",
}

EXPECTED_LIMITATIONS_V5_3 = [
    "V5.3 assemble uniquement un dataset supervise offline sur la fenetre historique continue validee par V5.0.",
    "V5.3 prepare des groupes walk-forward descriptifs mais ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def get_dataset_v3_8_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_8/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_V3_8}"
        / "dataset.parquet"
    )


def get_split_v3_8_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_8/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_V3_8}"
        / "splits.parquet"
    )


def get_dataset_v4_5_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v4_5/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_V4_5}"
        / "dataset.parquet"
    )


def get_split_v4_5_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v4_5/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_V4_5}"
        / "splits.parquet"
    )


def get_dataset_v5_3_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v5_3/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "dataset.parquet"
    )


def get_split_v5_3_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v5_3/datasets/offline_supervised"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "splits.parquet"
    )


VERSION_V6_1 = "V6.1"
DATASET_SCHEMA_VERSION_V6_1 = "V6.1"
TIMEFRAMES_V6_1 = ["1m", "5m", "15m", "1h"]

MANIFEST_PATH_V6_1 = Path("reports/manifests/advanced_ohlcv_offline_supervised_dataset_v6_1_manifest.json")
REPORT_JSON_PATH_V6_1 = Path("reports/datasets/advanced_ohlcv_offline_supervised_dataset_v6_1.json")
REPORT_MD_PATH_V6_1 = Path("reports/datasets/advanced_ohlcv_offline_supervised_dataset_v6_1.md")
DATACARD_MD_PATH_V6_1 = Path("reports/datasets/advanced_ohlcv_offline_supervised_dataset_v6_1_datacard.md")
DOC_PATH_V6_1 = Path("docs/advanced_ohlcv_offline_supervised_dataset_v6_1.md")

ADVANCED_DATASET_FEATURE_COLUMNS_V6_1 = [
    *ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0,
    *ADVANCED_OHLCV_AUDIT_COLUMNS_V6_0,
]

DATASET_COLUMNS_V6_1 = [
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
    *ADVANCED_DATASET_FEATURE_COLUMNS_V6_1,
    *LABEL_VALUE_COLUMNS,
    "split",
    "split_order",
    "purge_embargo_group",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
]

SPLIT_COLUMNS_V6_1 = [*JOIN_KEYS, "split", "split_order", "purge_embargo_group", "walk_forward_group"]

SPLIT_POLICY_V6_1 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v6_1_preview",
    "walk_forward_grouping": "calendar_quarter",
}

FORBIDDEN_DATASET_COLUMNS_EXACT_V6_1 = [
    "prediction",
    "predicted",
    "model_score",
    "score_ml",
    "alpha",
    "signal",
    "trading_signal",
    "strategy_signal",
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

EXPECTED_LIMITATIONS_V6_1 = [
    "V6.1 assemble uniquement un dataset supervise offline a partir des advanced OHLCV features V6.0 et labels V5.2.",
    "V6.1 prepare des groupes walk-forward descriptifs mais ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def get_dataset_v6_1_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v6_1/datasets/offline_supervised_advanced_ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "dataset.parquet"
    )


def get_split_v6_1_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v6_1/datasets/offline_supervised_advanced_ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "splits.parquet"
    )


VERSION_V7_3 = "V7.3"
DATASET_SCHEMA_VERSION_V7_3 = "DATASET_COLUMNS_V7_3"
TIMEFRAMES_V7_3 = ["1m", "5m", "15m", "1h"]
EXPECTED_ROWS_V7_3 = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720}
EXPECTED_SPLIT_COUNTS_V7_3 = {
    "1m": {"train": 25920, "validation": 8640, "test": 8640},
    "5m": {"train": 5184, "validation": 1728, "test": 1728},
    "15m": {"train": 1728, "validation": 576, "test": 576},
    "1h": {"train": 432, "validation": 144, "test": 144},
}

MANIFEST_PATH_V7_3 = Path("reports/manifests/ohlcv_trades_offline_supervised_dataset_v7_3_manifest.json")
REPORT_JSON_PATH_V7_3 = Path("reports/datasets/ohlcv_trades_offline_supervised_dataset_v7_3.json")
REPORT_MD_PATH_V7_3 = Path("reports/datasets/ohlcv_trades_offline_supervised_dataset_v7_3.md")
DATACARD_MD_PATH_V7_3 = Path("reports/datasets/ohlcv_trades_offline_supervised_dataset_v7_3_datacard.md")
DOC_PATH_V7_3 = Path("docs/ohlcv_trades_offline_supervised_dataset_v7_3.md")

OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_3 = [
    column for column in OHLCV_TRADES_FEATURE_COLUMNS_V7_2 if column not in OHLCV_TRADES_METADATA_COLUMNS_V7_2
]

DATASET_COLUMNS_V7_3 = [
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
    *OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_3,
    *LABEL_VALUE_COLUMNS,
    "split",
    "split_order",
    "purge_embargo_group",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
]

SPLIT_COLUMNS_V7_3 = [*JOIN_KEYS, "split", "split_order", "purge_embargo_group", "walk_forward_group"]

SPLIT_POLICY_V7_3 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v7_3_preview",
    "walk_forward_grouping": "seven_day_windows",
}

FORBIDDEN_DATASET_COLUMNS_EXACT_V7_3 = [
    "prediction",
    "predicted",
    "model_score",
    "score_ml",
    "alpha",
    "signal",
    "trading_signal",
    "strategy_signal",
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

EXPECTED_LIMITATIONS_V7_3 = [
    "V7.3 assemble uniquement un dataset supervise offline OHLCV + aggTrades sur une fenetre bornee de 30 jours.",
    "V7.3 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def get_dataset_v7_3_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v7_3/datasets/offline_supervised_ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "dataset.parquet"
    )


def get_split_v7_3_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v7_3/datasets/offline_supervised_ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "splits.parquet"
    )


VERSION_V7_9 = "V7.9"
DATASET_SCHEMA_VERSION_V7_9 = "DATASET_COLUMNS_V7_9"
TIMEFRAMES_V7_9 = ["1m", "5m", "15m", "1h"]
EXPECTED_ROWS_V7_9 = {"1m": 129600, "5m": 25920, "15m": 8640, "1h": 2160}
EXPECTED_SPLIT_COUNTS_V7_9 = {
    "1m": {"train": 77760, "validation": 25920, "test": 25920},
    "5m": {"train": 15552, "validation": 5184, "test": 5184},
    "15m": {"train": 5184, "validation": 1728, "test": 1728},
    "1h": {"train": 1296, "validation": 432, "test": 432},
}

MANIFEST_PATH_V7_9 = Path("reports/manifests/ohlcv_trades_90d_offline_supervised_dataset_v7_9_manifest.json")
REPORT_JSON_PATH_V7_9 = Path("reports/datasets/ohlcv_trades_90d_offline_supervised_dataset_v7_9.json")
REPORT_MD_PATH_V7_9 = Path("reports/datasets/ohlcv_trades_90d_offline_supervised_dataset_v7_9.md")
DATACARD_MD_PATH_V7_9 = Path("reports/datasets/ohlcv_trades_90d_offline_supervised_dataset_v7_9_datacard.md")
DOC_PATH_V7_9 = Path("docs/ohlcv_trades_90d_offline_supervised_dataset_v7_9.md")

OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_9 = [
    column for column in OHLCV_TRADES_FEATURE_COLUMNS_V7_8 if column not in OHLCV_TRADES_METADATA_COLUMNS_V7_8
]

DATASET_COLUMNS_V7_9 = [
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
    *OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_9,
    *LABEL_VALUE_COLUMNS,
    "split",
    "split_order",
    "purge_embargo_group",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
]

SPLIT_COLUMNS_V7_9 = [*JOIN_KEYS, "split", "split_order", "purge_embargo_group", "walk_forward_group"]

SPLIT_POLICY_V7_9 = {
    "train_ratio": 0.6,
    "validation_ratio": 0.2,
    "test_ratio": 0.2,
    "shuffle": False,
    "purge_embargo": "none_v7_9_preview",
    "walk_forward_grouping": "calendar_month",
}

FORBIDDEN_DATASET_COLUMNS_EXACT_V7_9 = [
    "prediction",
    "predicted",
    "model_score",
    "score_ml",
    "alpha",
    "signal",
    "trading_signal",
    "strategy_signal",
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

EXPECTED_LIMITATIONS_V7_9 = [
    "V7.9 assemble uniquement un dataset supervise offline OHLCV + aggTrades sur une fenetre bornee de 90 jours.",
    "V7.9 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def get_dataset_v7_9_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v7_9/datasets/offline_supervised_ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "dataset.parquet"
    )


def get_split_v7_9_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v7_9/datasets/offline_supervised_ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "splits.parquet"
    )


def assert_source_schema_imports() -> None:
    missing_features = [column for column in FEATURE_VALUE_COLUMNS if column not in FEATURE_COLUMNS_V2_5]
    missing_labels = [column for column in LABEL_VALUE_COLUMNS if column not in LABEL_COLUMNS_V2_6]
    if missing_features or missing_labels:
        raise RuntimeError(
            f"V2.7 source schema mismatch: missing_features={missing_features}, missing_labels={missing_labels}"
        )
