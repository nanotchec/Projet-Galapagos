from __future__ import annotations

from pathlib import Path

from galapagos.datasets.schemas import (
    OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_3,
    OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_9,
    OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4,
    TARGET_TIMEFRAMES,
)
from galapagos.features.advanced_ohlcv_schemas import ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0
from galapagos.features.refined_ohlcv_trades_schemas import REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0

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


VERSION_V3_9 = "V3.9"
ML_SCHEMA_VERSION_V3_9 = "V3.9"
TARGET_NAME_V3_9 = "up_down_flat_h1"
RANDOM_SEED_V3_9 = 42
TARGET_CLASSES_V3_9 = ["DOWN", "FLAT", "UP"]
MODEL_NAMES_V3_9 = [
    "majority_class_baseline",
    "random_seeded_baseline",
    "logistic_regression",
    "decision_tree_depth_2",
]
TIMEFRAMES_V3_9 = ["1m", "5m", "15m", "1h"]
EXPECTED_DATASET_ROWS_V3_9 = {"1m": 129600, "5m": 25920, "15m": 8640, "1h": 2160}
WINDOW_V3_9 = "2024-01-01_2024-03-30"

MANIFEST_PATH_V3_9 = Path("reports/manifests/expanded_offline_ml_research_v3_9_manifest.json")
REPORT_JSON_PATH_V3_9 = Path("reports/ml/expanded_offline_ml_research_v3_9.json")
REPORT_MD_PATH_V3_9 = Path("reports/ml/expanded_offline_ml_research_v3_9.md")
SCORES_JSON_PATH_V3_9 = Path("reports/ml/expanded_offline_research_scores_v3_9.json")
SCORES_MD_PATH_V3_9 = Path("reports/ml/expanded_offline_research_scores_v3_9.md")
DOC_PATH_V3_9 = Path("docs/expanded_offline_ml_research_v3_9.md")

ALLOWED_FEATURE_COLUMNS_V3_9 = ALLOWED_FEATURE_COLUMNS_V3_3.copy()
FORBIDDEN_FEATURE_TERMS_V3_9 = FORBIDDEN_FEATURE_TERMS_V3_3.copy()
FORBIDDEN_OUTPUT_TERMS_V3_9 = FORBIDDEN_OUTPUT_TERMS_V3_3.copy()
FORBIDDEN_METRIC_TERMS_V3_9 = FORBIDDEN_METRIC_TERMS_V3_3.copy()
ML_SCORE_COLUMNS_V3_9 = ML_SCORE_COLUMNS_V3_3.copy()

EXPECTED_LIMITATIONS_V3_9 = [
    "V3.9 entraine uniquement des baselines ML offline simples sur le dataset 90 jours V3.8 valide.",
    "V3.9 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]

SAFETY_FLAGS_V3_9 = {
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


def get_expanded_ml_score_path_v3_9(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_9/ml/offline_research"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_V3_9}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v3_9() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V3_9, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V4_6 = "V4.6"
ML_SCHEMA_VERSION_V4_6 = "V4.6"
TARGET_NAME_V4_6 = "up_down_flat_h1"
RANDOM_SEED_V4_6 = 42
TARGET_CLASSES_V4_6 = ["DOWN", "FLAT", "UP"]
MODEL_NAMES_V4_6 = MODEL_NAMES_V3_9.copy()
TIMEFRAMES_V4_6 = ["1m", "5m", "15m", "1h"]
EXPECTED_DATASET_ROWS_V4_6 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}
WINDOW_V4_6 = "2024-01-01_2024-12-31"

MANIFEST_PATH_V4_6 = Path("reports/manifests/one_year_offline_ml_research_v4_6_manifest.json")
REPORT_JSON_PATH_V4_6 = Path("reports/ml/one_year_offline_ml_research_v4_6.json")
REPORT_MD_PATH_V4_6 = Path("reports/ml/one_year_offline_ml_research_v4_6.md")
SCORES_JSON_PATH_V4_6 = Path("reports/ml/one_year_offline_research_scores_v4_6.json")
SCORES_MD_PATH_V4_6 = Path("reports/ml/one_year_offline_research_scores_v4_6.md")
DOC_PATH_V4_6 = Path("docs/one_year_offline_ml_research_v4_6.md")

ALLOWED_FEATURE_COLUMNS_V4_6 = ALLOWED_FEATURE_COLUMNS_V3_9.copy()
FORBIDDEN_FEATURE_TERMS_V4_6 = FORBIDDEN_FEATURE_TERMS_V3_9.copy()
FORBIDDEN_OUTPUT_TERMS_V4_6 = FORBIDDEN_OUTPUT_TERMS_V3_9.copy()
FORBIDDEN_METRIC_TERMS_V4_6 = FORBIDDEN_METRIC_TERMS_V3_9.copy()
ML_SCORE_COLUMNS_V4_6 = ML_SCORE_COLUMNS_V3_9.copy()

EXPECTED_LIMITATIONS_V4_6 = [
    "V4.6 entraine uniquement des baselines ML offline simples sur le dataset 1 an V4.5 valide.",
    "V4.6 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]

SAFETY_FLAGS_V4_6 = {
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


def get_one_year_ml_score_path_v4_6(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v4_6/ml/offline_research"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_V4_6}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v4_6() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V4_6, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V5_4 = "V5.4"
ML_SCHEMA_VERSION_V5_4 = "V5.4"
TARGET_NAME_V5_4 = "up_down_flat_h1"
RANDOM_SEED_V5_4 = 42
TARGET_CLASSES_V5_4 = TARGET_CLASSES_V4_6.copy()
MODEL_NAMES_V5_4 = MODEL_NAMES_V4_6.copy()
TIMEFRAMES_V5_4 = ["1m", "5m", "15m", "1h"]

MANIFEST_PATH_V5_4 = Path("reports/manifests/max_history_offline_ml_research_v5_4_manifest.json")
REPORT_JSON_PATH_V5_4 = Path("reports/ml/max_history_offline_ml_research_v5_4.json")
REPORT_MD_PATH_V5_4 = Path("reports/ml/max_history_offline_ml_research_v5_4.md")
SCORES_JSON_PATH_V5_4 = Path("reports/ml/max_history_offline_research_scores_v5_4.json")
SCORES_MD_PATH_V5_4 = Path("reports/ml/max_history_offline_research_scores_v5_4.md")
DOC_PATH_V5_4 = Path("docs/max_history_offline_ml_research_v5_4.md")

ALLOWED_FEATURE_COLUMNS_V5_4 = ALLOWED_FEATURE_COLUMNS_V4_6.copy()
FORBIDDEN_FEATURE_TERMS_V5_4 = [*FORBIDDEN_FEATURE_TERMS_V4_6, "walk_forward_group"]
FORBIDDEN_OUTPUT_TERMS_V5_4 = FORBIDDEN_OUTPUT_TERMS_V4_6.copy()
FORBIDDEN_METRIC_TERMS_V5_4 = FORBIDDEN_METRIC_TERMS_V4_6.copy()
ML_SCORE_COLUMNS_V5_4 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "split",
    "walk_forward_group",
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

EXPECTED_LIMITATIONS_V5_4 = [
    "V5.4 entraine uniquement des baselines ML offline simples sur le dataset historique V5.3 valide.",
    "V5.4 produit des metriques descriptives par split et par groupe walk-forward, mais ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]

SAFETY_FLAGS_V5_4 = {
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


def get_max_history_ml_score_path_v5_4(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v5_4/ml/offline_research"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v5_4() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V5_4, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V6_2 = "V6.2"
ML_SCHEMA_VERSION_V6_2 = "V6.2"
TARGET_NAME_V6_2 = "up_down_flat_h1"
RANDOM_SEED_V6_2 = 42
TARGET_CLASSES_V6_2 = TARGET_CLASSES_V5_4.copy()
MODEL_NAMES_V6_2 = MODEL_NAMES_V5_4.copy()
TIMEFRAMES_V6_2 = ["1m", "5m", "15m", "1h"]

MANIFEST_PATH_V6_2 = Path("reports/manifests/advanced_ohlcv_offline_ml_research_v6_2_manifest.json")
REPORT_JSON_PATH_V6_2 = Path("reports/ml/advanced_ohlcv_offline_ml_research_v6_2.json")
REPORT_MD_PATH_V6_2 = Path("reports/ml/advanced_ohlcv_offline_ml_research_v6_2.md")
SCORES_JSON_PATH_V6_2 = Path("reports/ml/advanced_ohlcv_offline_research_scores_v6_2.json")
SCORES_MD_PATH_V6_2 = Path("reports/ml/advanced_ohlcv_offline_research_scores_v6_2.md")
DOC_PATH_V6_2 = Path("docs/advanced_ohlcv_offline_ml_research_v6_2.md")

ALLOWED_FEATURE_COLUMNS_V6_2 = ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0.copy()
FORBIDDEN_FEATURE_PREFIXES_V6_2 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]
FORBIDDEN_FEATURE_EXACT_V6_2 = [
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
    "target",
    "warmup_row",
    "tail_row",
    "split",
    "split_order",
    "purge_embargo_group",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
    "advanced_feature_null_count",
    "advanced_feature_error_count",
    "signal",
    "trading_signal",
    "strategy_signal",
    "order",
    "strategy",
    "trade_decision",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
]
FORBIDDEN_OUTPUT_COLUMNS_EXACT_V6_2 = [
    "signal",
    "trading_signal",
    "strategy_signal",
    "order",
    "strategy",
    "entry",
    "exit",
    "position",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
    "return_strategy",
]
FORBIDDEN_METRIC_TERMS_V6_2 = [
    "pnl",
    "sharpe",
    "drawdown",
    "equity",
    "equity_curve",
    "profit",
    "profit_factor",
    "win_rate_trading",
    "return_strategy",
]
ML_SCORE_COLUMNS_V6_2 = ML_SCORE_COLUMNS_V5_4.copy()

EXPECTED_LIMITATIONS_V6_2 = [
    "V6.2 entraine uniquement des baselines ML offline simples sur le dataset V6.1 avec advanced OHLCV features.",
    "V6.2 compare descriptivement les resultats aux baselines V5.4 simple OHLCV si disponibles, sans produire de backtest, de strategie, de signal de trading ni d'ordre.",
]

SAFETY_FLAGS_V6_2 = {
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


def get_advanced_ohlcv_ml_score_path_v6_2(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v6_2/ml/offline_research_advanced_ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v6_2() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V6_2, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V7_4 = "V7.4"
ML_SCHEMA_VERSION_V7_4 = "V7.4"
TARGET_NAME_V7_4 = "up_down_flat_h1"
RANDOM_SEED_V7_4 = 42
TARGET_CLASSES_V7_4 = TARGET_CLASSES_V5_4.copy()
MODEL_NAMES_V7_4 = MODEL_NAMES_V5_4.copy()
TIMEFRAMES_V7_4 = ["1m", "5m", "15m", "1h"]

MANIFEST_PATH_V7_4 = Path("reports/manifests/ohlcv_trades_offline_ml_research_v7_4_manifest.json")
REPORT_JSON_PATH_V7_4 = Path("reports/ml/ohlcv_trades_offline_ml_research_v7_4.json")
REPORT_MD_PATH_V7_4 = Path("reports/ml/ohlcv_trades_offline_ml_research_v7_4.md")
SCORES_JSON_PATH_V7_4 = Path("reports/ml/ohlcv_trades_offline_research_scores_v7_4.json")
SCORES_MD_PATH_V7_4 = Path("reports/ml/ohlcv_trades_offline_research_scores_v7_4.md")
DOC_PATH_V7_4 = Path("docs/ohlcv_trades_offline_ml_research_v7_4.md")

ALLOWED_FEATURE_COLUMNS_V7_4 = [
    column
    for column in OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_3
    if column not in {"warmup_row", "trades_feature_null_count", "trades_feature_error_count"}
]
FORBIDDEN_FEATURE_PREFIXES_V7_4 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]
FORBIDDEN_FEATURE_EXACT_V7_4 = [
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
    "target",
    "warmup_row",
    "tail_row",
    "split",
    "split_order",
    "purge_embargo_group",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
    "trades_feature_null_count",
    "trades_feature_error_count",
    "signal",
    "trading_signal",
    "strategy_signal",
    "order",
    "strategy",
    "trade_decision",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
]
FORBIDDEN_OUTPUT_COLUMNS_EXACT_V7_4 = FORBIDDEN_OUTPUT_COLUMNS_EXACT_V6_2.copy()
FORBIDDEN_METRIC_TERMS_V7_4 = FORBIDDEN_METRIC_TERMS_V6_2.copy()
ML_SCORE_COLUMNS_V7_4 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "split",
    "walk_forward_group",
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

EXPECTED_LIMITATIONS_V7_4 = [
    "V7.4 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades V7.3.",
    "V7.4 utilise une fenetre bornee de 30 jours et ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]

SAFETY_FLAGS_V7_4 = {
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


def get_ohlcv_trades_ml_score_path_v7_4(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v7_4/ml/offline_research_ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v7_4() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V7_4, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V8_0 = "V8.0"
ML_SCHEMA_VERSION_V8_0 = "V8.0"
TARGET_NAME_V8_0 = "up_down_flat_h1"
RANDOM_SEED_V8_0 = 42
TARGET_CLASSES_V8_0 = TARGET_CLASSES_V7_4.copy()
MODEL_NAMES_V8_0 = MODEL_NAMES_V7_4.copy()
TIMEFRAMES_V8_0 = ["1m", "5m", "15m", "1h"]

MANIFEST_PATH_V8_0 = Path("reports/manifests/ohlcv_trades_90d_offline_ml_research_v8_0_manifest.json")
REPORT_JSON_PATH_V8_0 = Path("reports/ml/ohlcv_trades_90d_offline_ml_research_v8_0.json")
REPORT_MD_PATH_V8_0 = Path("reports/ml/ohlcv_trades_90d_offline_ml_research_v8_0.md")
SCORES_JSON_PATH_V8_0 = Path("reports/ml/ohlcv_trades_90d_offline_research_scores_v8_0.json")
SCORES_MD_PATH_V8_0 = Path("reports/ml/ohlcv_trades_90d_offline_research_scores_v8_0.md")
DOC_PATH_V8_0 = Path("docs/ohlcv_trades_90d_offline_ml_research_v8_0.md")

ALLOWED_FEATURE_COLUMNS_V8_0 = [
    column
    for column in OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V7_9
    if column not in {"warmup_row", "trades_feature_null_count", "trades_feature_error_count"}
]
FORBIDDEN_FEATURE_PREFIXES_V8_0 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]
FORBIDDEN_FEATURE_EXACT_V8_0 = [
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
    "target",
    "warmup_row",
    "tail_row",
    "split",
    "split_order",
    "purge_embargo_group",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
    "trades_feature_null_count",
    "trades_feature_error_count",
    "signal",
    "trading_signal",
    "strategy_signal",
    "order",
    "strategy",
    "trade_decision",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
]
FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_0 = FORBIDDEN_OUTPUT_COLUMNS_EXACT_V7_4.copy()
FORBIDDEN_METRIC_TERMS_V8_0 = FORBIDDEN_METRIC_TERMS_V7_4.copy()
ML_SCORE_COLUMNS_V8_0 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "split",
    "walk_forward_group",
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

EXPECTED_LIMITATIONS_V8_0 = [
    "V8.0 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades 90 jours V7.9.",
    "V8.0 produit une robustesse descriptive et une falsification offline, sans backtest, sans strategie, sans signal de trading et sans ordre.",
    "La fenetre de 90 jours reste insuffisante pour conclure a une robustesse statistique forte.",
]

SAFETY_FLAGS_V8_0 = {
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


def get_ohlcv_trades_ml_score_path_v8_0(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v8_0/ml/offline_research_ohlcv_trades_90d"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v8_0() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V8_0, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V8_5 = "V8.5"
ML_SCHEMA_VERSION_V8_5 = "V8.5"
TARGET_NAME_V8_5 = "up_down_flat_h1"
RANDOM_SEED_V8_5 = 42
TARGET_CLASSES_V8_5 = TARGET_CLASSES_V7_4.copy()
MODEL_NAMES_V8_5 = MODEL_NAMES_V7_4.copy()
TIMEFRAMES_V8_5 = ["1m", "5m", "15m", "1h"]

MANIFEST_PATH_V8_5 = Path("reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json")
REPORT_JSON_PATH_V8_5 = Path("reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.json")
REPORT_MD_PATH_V8_5 = Path("reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.md")
SCORES_JSON_PATH_V8_5 = Path("reports/ml/ohlcv_trades_1y_offline_research_scores_v8_5.json")
SCORES_MD_PATH_V8_5 = Path("reports/ml/ohlcv_trades_1y_offline_research_scores_v8_5.md")
DOC_PATH_V8_5 = Path("docs/ohlcv_trades_1y_offline_ml_research_v8_5.md")

ALLOWED_FEATURE_COLUMNS_V8_5 = [
    column
    for column in OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4
    if column not in {"warmup_row", "trades_feature_null_count", "trades_feature_error_count"}
]
FORBIDDEN_FEATURE_PREFIXES_V8_5 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]
FORBIDDEN_FEATURE_EXACT_V8_5 = [
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
    "target",
    "warmup_row",
    "tail_row",
    "split",
    "split_order",
    "purge_embargo_group",
    "walk_forward_group",
    "dataset_null_count",
    "dataset_error_count",
    "trades_feature_null_count",
    "trades_feature_error_count",
    "signal",
    "trading_signal",
    "strategy_signal",
    "order",
    "strategy",
    "trade_decision",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
]
FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_5 = FORBIDDEN_OUTPUT_COLUMNS_EXACT_V7_4.copy()
FORBIDDEN_METRIC_TERMS_V8_5 = FORBIDDEN_METRIC_TERMS_V7_4.copy()
ML_SCORE_COLUMNS_V8_5 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "split",
    "walk_forward_group",
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

EXPECTED_LIMITATIONS_V8_5 = [
    "V8.5 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades 1 an V8.4.",
    "V8.5 produit des metriques descriptives et non actionnables, sans backtest, sans strategie, sans signal de trading et sans ordre.",
]

SAFETY_FLAGS_V8_5 = {
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


def get_ohlcv_trades_ml_score_path_v8_5(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v8_5/ml/offline_research_ohlcv_trades_1y"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v8_5() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V8_5, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V8_7 = "V8.7"
ML_SCHEMA_VERSION_V8_7 = "V8.7"
TARGET_NAME_V8_7 = TARGET_NAME_V8_5
RANDOM_SEED_V8_7 = RANDOM_SEED_V8_5
LABEL_SHUFFLE_RANDOM_SEED_V8_7 = 123
TARGET_CLASSES_V8_7 = TARGET_CLASSES_V8_5.copy()
MODEL_NAMES_V8_7 = MODEL_NAMES_V8_5.copy()
TIMEFRAMES_V8_7 = TIMEFRAMES_V8_5.copy()

MANIFEST_PATH_V8_7 = Path("reports/manifests/strict_walk_forward_validation_v8_7_manifest.json")
REPORT_JSON_PATH_V8_7 = Path("reports/ml/strict_walk_forward_validation_v8_7.json")
REPORT_MD_PATH_V8_7 = Path("reports/ml/strict_walk_forward_validation_v8_7.md")
SCORES_JSON_PATH_V8_7 = Path("reports/ml/strict_walk_forward_scores_v8_7.json")
SCORES_MD_PATH_V8_7 = Path("reports/ml/strict_walk_forward_scores_v8_7.md")
DOC_PATH_V8_7 = Path("docs/strict_walk_forward_validation_v8_7.md")

ALLOWED_FEATURE_COLUMNS_V8_7 = ALLOWED_FEATURE_COLUMNS_V8_5.copy()
FORBIDDEN_FEATURE_PREFIXES_V8_7 = FORBIDDEN_FEATURE_PREFIXES_V8_5.copy()
FORBIDDEN_FEATURE_EXACT_V8_7 = [
    *FORBIDDEN_FEATURE_EXACT_V8_5,
    "fold_id",
    "fold_role",
    "fold_order",
    "is_embargoed",
    "is_purged",
]
FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_7 = FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_5.copy()
FORBIDDEN_METRIC_TERMS_V8_7 = FORBIDDEN_METRIC_TERMS_V8_5.copy()
ML_SCORE_COLUMNS_V8_7 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "fold_id",
    "fold_role",
    "fold_order",
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
WALK_FORWARD_FOLD_COLUMNS_V8_7 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "fold_id",
    "fold_role",
    "fold_order",
    "is_embargoed",
    "is_purged",
    "walk_forward_policy_version",
]

EXPECTED_LIMITATIONS_V8_7 = [
    "V8.7 produit une validation walk-forward offline stricte des baselines ML sur le dataset OHLCV + aggTrades 1 an V8.4.",
    "V8.7 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
    "Les resultats restent descriptifs et ne valident pas une exploitation trading.",
]

SAFETY_FLAGS_V8_7 = {
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


def get_strict_walk_forward_score_path_v8_7(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v8_7/ml/strict_walk_forward"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "walk_forward_scores.parquet"
    )


def get_strict_walk_forward_folds_path_v8_7(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v8_7/ml/strict_walk_forward"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "folds.parquet"
    )


def get_feature_columns_sha256_v8_7() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V8_7, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V9_2 = "V9.2"
ML_SCHEMA_VERSION_V9_2 = "V9.2"
TARGET_NAME_V9_2 = TARGET_NAME_V8_5
RANDOM_SEED_V9_2 = RANDOM_SEED_V8_5
TARGET_CLASSES_V9_2 = TARGET_CLASSES_V8_5.copy()
MODEL_NAMES_V9_2 = MODEL_NAMES_V8_5.copy()
TIMEFRAMES_V9_2 = TIMEFRAMES_V8_5.copy()

MANIFEST_PATH_V9_2 = Path("reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json")
REPORT_JSON_PATH_V9_2 = Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json")
REPORT_MD_PATH_V9_2 = Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.md")
SCORES_JSON_PATH_V9_2 = Path("reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.json")
SCORES_MD_PATH_V9_2 = Path("reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.md")
DOC_PATH_V9_2 = Path("docs/refined_ohlcv_trades_offline_ml_research_v9_2.md")

ALLOWED_FEATURE_COLUMNS_V9_2 = REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0.copy()
FORBIDDEN_FEATURE_PREFIXES_V9_2 = FORBIDDEN_FEATURE_PREFIXES_V8_5.copy()
FORBIDDEN_FEATURE_EXACT_V9_2 = [
    *FORBIDDEN_FEATURE_EXACT_V8_5,
    "refined_feature_null_count",
    "refined_feature_error_count",
]
FORBIDDEN_OUTPUT_COLUMNS_EXACT_V9_2 = FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_5.copy()
FORBIDDEN_METRIC_TERMS_V9_2 = FORBIDDEN_METRIC_TERMS_V8_5.copy()
ML_SCORE_COLUMNS_V9_2 = ML_SCORE_COLUMNS_V8_5.copy()

EXPECTED_LIMITATIONS_V9_2 = [
    "V9.2 entraine uniquement des baselines ML offline simples sur le dataset raffine V9.1.",
    "V9.2 produit des metriques descriptives et non actionnables, sans backtest, sans strategie, sans signal de trading et sans ordre.",
]

SAFETY_FLAGS_V9_2 = SAFETY_FLAGS_V8_5.copy()


def get_refined_ohlcv_trades_ml_score_path_v9_2(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v9_2/ml/refined_offline_research_ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v9_2() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V9_2, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


VERSION_V9_3 = "V9.3"
ML_SCHEMA_VERSION_V9_3 = "V9.3"
TARGET_NAME_V9_3 = TARGET_NAME_V9_2
RANDOM_SEED_V9_3 = RANDOM_SEED_V9_2
LABEL_SHUFFLE_RANDOM_SEED_V9_3 = 123
TARGET_CLASSES_V9_3 = TARGET_CLASSES_V9_2.copy()
MODEL_NAMES_V9_3 = MODEL_NAMES_V9_2.copy()
TIMEFRAMES_V9_3 = TIMEFRAMES_V9_2.copy()

MANIFEST_PATH_V9_3 = Path("reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json")
REPORT_JSON_PATH_V9_3 = Path("reports/ml/refined_strict_walk_forward_validation_v9_3.json")
REPORT_MD_PATH_V9_3 = Path("reports/ml/refined_strict_walk_forward_validation_v9_3.md")
SCORES_JSON_PATH_V9_3 = Path("reports/ml/refined_strict_walk_forward_scores_v9_3.json")
SCORES_MD_PATH_V9_3 = Path("reports/ml/refined_strict_walk_forward_scores_v9_3.md")
DOC_PATH_V9_3 = Path("docs/refined_strict_walk_forward_validation_v9_3.md")

ALLOWED_FEATURE_COLUMNS_V9_3 = ALLOWED_FEATURE_COLUMNS_V9_2.copy()
FORBIDDEN_FEATURE_PREFIXES_V9_3 = FORBIDDEN_FEATURE_PREFIXES_V9_2.copy()
FORBIDDEN_FEATURE_EXACT_V9_3 = [
    *FORBIDDEN_FEATURE_EXACT_V9_2,
    "fold_id",
    "fold_role",
    "fold_order",
    "is_embargoed",
    "is_purged",
]
FORBIDDEN_OUTPUT_COLUMNS_EXACT_V9_3 = FORBIDDEN_OUTPUT_COLUMNS_EXACT_V9_2.copy()
FORBIDDEN_METRIC_TERMS_V9_3 = FORBIDDEN_METRIC_TERMS_V9_2.copy()
ML_SCORE_COLUMNS_V9_3 = ML_SCORE_COLUMNS_V8_7.copy()
WALK_FORWARD_FOLD_COLUMNS_V9_3 = WALK_FORWARD_FOLD_COLUMNS_V8_7.copy()

EXPECTED_LIMITATIONS_V9_3 = [
    "V9.3 produit une validation walk-forward offline stricte des baselines ML raffinees sur le dataset V9.1.",
    "V9.3 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
    "Les resultats restent descriptifs et ne valident pas une exploitation trading.",
]

SAFETY_FLAGS_V9_3 = SAFETY_FLAGS_V8_7.copy()


def get_refined_strict_walk_forward_score_path_v9_3(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v9_3/ml/refined_strict_walk_forward"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "walk_forward_scores.parquet"
    )


def get_refined_strict_walk_forward_folds_path_v9_3(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v9_3/ml/refined_strict_walk_forward"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "folds.parquet"
    )


def get_feature_columns_sha256_v9_3() -> str:
    import hashlib
    import json

    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V9_3, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
