from __future__ import annotations

from pathlib import Path

from galapagos.datasets.schemas import TARGET_TIMEFRAMES

VERSION = "V2.8"
CORRECTION_VERSION = "V2.8.4"
ML_SCHEMA_VERSION = "V2.8"
TARGET_NAME = "up_down_flat_h1"
RANDOM_SEED = 42
TARGET_CLASSES = ["DOWN", "FLAT", "UP"]
MODEL_NAMES = [
    "majority_class_baseline",
    "random_seeded_baseline",
    "logistic_regression",
    "decision_tree_depth_2",
]

MANIFEST_PATH = Path("reports/manifests/offline_ml_research_v2_8_manifest.json")
REPORT_JSON_PATH = Path("reports/ml/offline_ml_research_v2_8.json")
REPORT_MD_PATH = Path("reports/ml/offline_ml_research_v2_8.md")
SCORES_JSON_PATH = Path("reports/ml/offline_research_scores_v2_8.json")
SCORES_MD_PATH = Path("reports/ml/offline_research_scores_v2_8.md")

ALLOWED_FEATURE_COLUMNS_V2_8 = [
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
    "feature_null_count",
    "feature_error_count",
]

FORBIDDEN_FEATURE_TERMS_V2_8 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
    "target",
    "split",
    "signal",
    "order",
    "strategy",
    "pnl",
    "profit",
    "backtest",
    "position_size",
    "dataset_null_count",
    "dataset_error_count",
    "warmup_row",
    "tail_row",
]

FORBIDDEN_OUTPUT_TERMS_V2_8 = [
    "trading_signal",
    "signal",
    "order",
    "strategy",
    "entry",
    "exit",
    "position",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "sharpe",
    "drawdown",
    "equity",
    "return_strategy",
]

FORBIDDEN_METRIC_TERMS_V2_8 = [
    "pnl",
    "sharpe",
    "drawdown",
    "equity",
    "profit",
    "profit_factor",
    "win_rate_trading",
    "return_strategy",
]

ML_SCORE_COLUMNS_V2_8 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "split",
    "ml_run_id",
    "model_name",
    "target_name",
    "dataset_sha256",
    "feature_columns_sha256",
    "ml_schema_version",
    "target_value",
    "research_predicted_class",
    "research_probability_down",
    "research_probability_flat",
    "research_probability_up",
    "prediction_available_ts",
    "row_valid_for_ml",
    "ml_null_count",
    "ml_error_count",
]

EXPECTED_LIMITATIONS_V2_8 = [
    "V2.8 entraine uniquement des baselines ML offline simples sur le dataset V2.7 valide.",
    "V2.8 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]

SAFETY_FLAGS_V2_8 = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "ml_enabled": True,
    "labels_enabled": True,
    "dataset_enabled": True,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}


def get_ml_score_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/gold/ml/offline_research"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "year=2024"
        / "month=01"
        / "ml-scores-2024-01-15.parquet"
    )


def get_feature_columns_sha256() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V2_8, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V3_3 = "V3.3"
ML_SCHEMA_VERSION_V3_3 = "V3.3"
TARGET_NAME_V3_3 = "up_down_flat_h1"
RANDOM_SEED_V3_3 = 42
TARGET_CLASSES_V3_3 = ["DOWN", "FLAT", "UP"]
MODEL_NAMES_V3_3 = [
    "majority_class_baseline",
    "random_seeded_baseline",
    "logistic_regression",
    "decision_tree_depth_2",
]
TIMEFRAMES_V3_3 = ["1m", "5m", "15m", "1h"]
EXPECTED_DATASET_ROWS_V3_3 = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}

MANIFEST_PATH_V3_3 = Path("reports/manifests/multi_day_offline_ml_research_v3_3_manifest.json")
REPORT_JSON_PATH_V3_3 = Path("reports/ml/multi_day_offline_ml_research_v3_3.json")
REPORT_MD_PATH_V3_3 = Path("reports/ml/multi_day_offline_ml_research_v3_3.md")
SCORES_JSON_PATH_V3_3 = Path("reports/ml/multi_day_offline_research_scores_v3_3.json")
SCORES_MD_PATH_V3_3 = Path("reports/ml/multi_day_offline_research_scores_v3_3.md")
DOC_PATH_V3_3 = Path("docs/multi_day_offline_ml_research_v3_3.md")

ALLOWED_FEATURE_COLUMNS_V3_3 = [
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
    "feature_null_count",
    "feature_error_count",
]

FORBIDDEN_FEATURE_TERMS_V3_3 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
    "target",
    "split",
    "signal",
    "order",
    "strategy",
    "pnl",
    "profit",
    "backtest",
    "position_size",
    "dataset_null_count",
    "dataset_error_count",
    "warmup_row",
    "tail_row",
]

FORBIDDEN_OUTPUT_TERMS_V3_3 = [
    "trading_signal",
    "signal",
    "order",
    "strategy",
    "entry",
    "exit",
    "position",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "sharpe",
    "drawdown",
    "equity",
    "return_strategy",
]

FORBIDDEN_METRIC_TERMS_V3_3 = [
    "pnl",
    "sharpe",
    "drawdown",
    "equity",
    "profit",
    "profit_factor",
    "win_rate_trading",
    "return_strategy",
]

ML_SCORE_COLUMNS_V3_3 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "split",
    "ml_run_id",
    "model_name",
    "target_name",
    "dataset_sha256",
    "feature_columns_sha256",
    "ml_schema_version",
    "target_value",
    "research_predicted_class",
    "research_probability_down",
    "research_probability_flat",
    "research_probability_up",
    "prediction_available_ts",
    "row_valid_for_ml",
    "ml_null_count",
    "ml_error_count",
]

EXPECTED_LIMITATIONS_V3_3 = [
    "V3.3 entraine uniquement des baselines ML offline simples sur le dataset multi-day V3.2 valide.",
    "V3.3 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]

SAFETY_FLAGS_V3_3 = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "ml_enabled": True,
    "labels_enabled": True,
    "dataset_enabled": True,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}


def get_multi_day_ml_score_path_v3_3(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_3/ml/offline_research"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "window=2024-01-15_2024-01-21"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v3_3() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V3_3, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
