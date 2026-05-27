from __future__ import annotations

from pathlib import Path


VERSION_V9_12 = "V9.12"
LABEL_SCHEMA_VERSION_V9_12 = "HORIZON_EVENT_LABEL_COLUMNS_V9_12"
TIMEFRAMES_V9_12 = ["1m", "5m", "15m", "1h"]
TIMEFRAME_MINUTES_V9_12 = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
WINDOW_START_V9_12 = "2023-03-25"
WINDOW_END_V9_12 = "2024-03-24"
TOTAL_DAYS_V9_12 = 366
EXPECTED_ROWS_V9_12 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}

HORIZON_CANDIDATES_V9_12 = {
    "h2": {"target_name": "up_down_flat_volnorm_h2", "duration_minutes": 120},
    "h4": {"target_name": "up_down_flat_volnorm_h4", "duration_minutes": 240},
    "h8": {"target_name": "up_down_flat_volnorm_h8", "duration_minutes": 480},
}
HORIZON_MULTIPLIERS_V9_12 = [0.75, 1.00, 1.25]
SELECTED_HORIZON_V9_12 = "h4"
SELECTED_HORIZON_MULTIPLIER_V9_12 = 1.25
EVENT_HORIZON_NAME_V9_12 = "h8"
EVENT_THRESHOLD_MULTIPLIER_V9_12 = 3.0
CAUSAL_VOL_WINDOW_BARS_V9_12 = 30
CAUSAL_VOL_MIN_PERIODS_V9_12 = 10

INPUT_V9_11_DECISION = Path("reports/research_decisions/label_failure_analysis_v9_11.json")
INPUT_V9_11_MANIFEST = Path("reports/manifests/label_failure_analysis_v9_11_manifest.json")
INPUT_V9_6_LABEL_REPORT = Path("reports/labels/refined_volatility_normalized_labels_v9_6.json")
INPUT_V9_7_DATASET_REPORT = Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.json")
INPUT_V9_8_ML_REPORT = Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json")
INPUT_V9_9_WALK_FORWARD_REPORT = Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json")
INPUT_V9_10_DECISION = Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json")
INPUT_V9_5_DECISION = Path("reports/research_decisions/alternative_label_design_audit_v9_5.json")
INPUT_LATEST_METRICS = Path("reports/current/latest_metrics.json")
INPUT_LATEST_SUMMARY = Path("reports/current/latest_summary.md")
INPUT_PROJECT_STATE = Path("reports/PROJECT_STATE.json")

MANIFEST_PATH_V9_12 = Path("reports/manifests/horizon_event_label_redesign_v9_12_manifest.json")
REPORT_JSON_PATH_V9_12 = Path("reports/labels/horizon_event_label_redesign_v9_12.json")
REPORT_MD_PATH_V9_12 = Path("reports/labels/horizon_event_label_redesign_v9_12.md")
DATACARD_MD_PATH_V9_12 = Path("reports/labels/horizon_event_label_redesign_v9_12_datacard.md")
DOC_PATH_V9_12 = Path("docs/horizon_event_label_redesign_v9_12.md")

HORIZON_EVENT_LABEL_COLUMNS_V9_12 = [
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
    "source_label_design_version",
    "candidate_family",
    "target_name",
    "horizon_name",
    "horizon_duration_minutes",
    "future_log_return",
    "causal_vol_window_bars",
    "causal_vol_min_periods",
    "causal_realized_vol",
    "volatility_threshold_multiplier",
    "volatility_normalized_threshold",
    "up_down_flat_volnorm_h2",
    "up_down_flat_volnorm_h4",
    "up_down_flat_volnorm_h8",
    "event_based_label",
    "event_horizon_name",
    "event_threshold_multiplier",
    "event_valid",
    "label_valid",
    "label_invalid_reason",
    "warmup_row",
    "label_null_count",
    "label_error_count",
]

FORBIDDEN_LABEL_COLUMNS_V9_12 = {
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

ALLOWED_DECISIONS_V9_12 = {
    "label_redesign_candidate_horizon_extension_created",
    "label_redesign_candidate_event_based_created",
    "label_redesign_candidate_horizon_event_created_requires_review",
    "label_redesign_not_ready_missing_full_data",
    "label_redesign_not_ready_quality_failed",
    "stop_refined_label_branch",
}

FINDINGS_V9_12 = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

SAFETY_FLAGS_V9_12 = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

SAFETY_V9_12 = {
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
    "sidecars_created": False,
    "zip_fingerprints_created": False,
}

EXPECTED_LIMITATIONS_V9_12 = [
    "V9.12 cree et audite uniquement des candidats de labels horizon extension et event-based descriptifs.",
    "V9.12 ne lance aucun ML, aucun walk-forward, aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
    "Les candidats V9.12 ne prouvent aucun edge et doivent etre revalides dans une version future avant toute interpretation.",
]


def get_horizon_event_label_path_v9_12(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_12/labels/horizon_event_redesign"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_12}_{WINDOW_END_V9_12}"
        / "labels.parquet"
    )
