from __future__ import annotations

from pathlib import Path


VERSION_V9_6 = "V9.6"
LABEL_SCHEMA_VERSION_V9_6 = "REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6"
TIMEFRAMES_V9_6 = ["1m", "5m", "15m", "1h"]
WINDOW_START_V9_6 = "2023-03-25"
WINDOW_END_V9_6 = "2024-03-24"
TOTAL_DAYS_V9_6 = 366
EXPECTED_ROWS_V9_6 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}
TARGET_NAME_V9_6 = "up_down_flat_volnorm_h1"
HORIZON_NAME_V9_6 = "h1"
HORIZON_BARS_V9_6 = 1
CAUSAL_VOL_WINDOW_BARS_V9_6 = 30
CAUSAL_VOL_MIN_PERIODS_V9_6 = 10
PARAMETER_GRID_V9_6 = [0.50, 0.75, 1.00, 1.25]

INPUT_DECISION_V9_5 = Path("reports/research_decisions/alternative_label_design_audit_v9_5.json")
INPUT_DECISION_MANIFEST_V9_5 = Path("reports/manifests/alternative_label_design_audit_v9_5_manifest.json")
INPUT_DATASET_MANIFEST_V9_1 = Path("reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json")
MANIFEST_PATH_V9_6 = Path("reports/manifests/refined_volatility_normalized_labels_v9_6_manifest.json")
REPORT_JSON_PATH_V9_6 = Path("reports/labels/refined_volatility_normalized_labels_v9_6.json")
REPORT_MD_PATH_V9_6 = Path("reports/labels/refined_volatility_normalized_labels_v9_6.md")
DATACARD_MD_PATH_V9_6 = Path("reports/labels/refined_volatility_normalized_labels_v9_6_datacard.md")
DOC_PATH_V9_6 = Path("docs/refined_volatility_normalized_labels_v9_6.md")

REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "label_start_ts",
    "label_end_ts",
    "label_available_ts",
    "label_run_id",
    "label_schema_version",
    "source_dataset_version",
    "source_dataset_path",
    "source_label_design_version",
    "target_name",
    "horizon_name",
    "horizon_bars",
    "future_log_return",
    "causal_vol_window_bars",
    "causal_vol_min_periods",
    "causal_realized_vol",
    "volatility_threshold_multiplier",
    "volatility_normalized_threshold",
    "up_down_flat_volnorm_h1",
    "label_valid_volnorm_h1",
    "label_invalid_reason",
    "warmup_row",
    "label_null_count",
    "label_error_count",
]

FORBIDDEN_LABEL_COLUMNS_V9_6 = {
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

ALLOWED_DECISIONS_V9_6 = {
    "label_factory_candidate_created_volatility_normalized",
    "label_factory_not_ready_missing_full_data",
    "label_factory_not_ready_quality_failed",
    "label_factory_candidate_created_but_requires_review",
    "stop_refined_branch_label_factory_failed",
}

SAFETY_FLAGS_V9_6 = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "ml_enabled": False,
    "labels_enabled": True,
    "dataset_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
    "persistent_model_created": False,
}

FINDINGS_V9_6 = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

EXPECTED_LIMITATIONS_V9_6 = [
    "V9.6 cree uniquement des labels candidats volatility-normalized pour une evaluation de recherche offline.",
    "V9.6 ne lance aucun ML, aucun walk-forward, aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
    "Le candidat retenu est selectionne uniquement par qualite de distribution, causalite et disponibilite temporelle, jamais par performance de trading.",
]


def get_refined_volnorm_label_path_v9_6(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_6/labels/refined_volatility_normalized"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_6}_{WINDOW_END_V9_6}"
        / "labels.parquet"
    )
