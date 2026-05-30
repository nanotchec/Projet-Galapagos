from __future__ import annotations

from copy import deepcopy

from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37 import build_manifest_v9_37
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_validation import (
    validate_manifest_payload_v9_37,
    validate_report_payload_v9_37,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_schemas import (
    EXPECTED_ROWS_BY_TIMEFRAME,
    FEATURE_COLUMNS,
)


def test_v9_37_validator_accepts_created_with_warnings_payload() -> None:
    report = _report()
    manifest = build_manifest_v9_37(report)

    assert validate_report_payload_v9_37(report) == []
    assert validate_manifest_payload_v9_37(report, manifest) == []


def test_v9_37_validator_rejects_network_usage() -> None:
    report = _report()
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_37(report)

    assert any("network" in error for error in errors)


def test_v9_37_validator_rejects_labels_or_dataset() -> None:
    report = _report()
    report["labels_created"] = True

    errors = validate_report_payload_v9_37(report)

    assert any("labels" in error for error in errors)


def test_v9_37_validator_rejects_leakage_guard_failure() -> None:
    report = _report()
    report["leakage_guard"]["status"] = "FAIL"

    errors = validate_report_payload_v9_37(report)

    assert any("leakage" in error for error in errors)


def test_v9_37_validator_rejects_missing_timeframe() -> None:
    report = _report()
    report["timeframe_reports"].pop("1h")

    errors = validate_report_payload_v9_37(report)

    assert any("timeframe_reports" in error for error in errors)


def test_v9_37_manifest_mismatch_is_detected() -> None:
    report = _report()
    manifest = build_manifest_v9_37(report)
    manifest["feature_store_created"] = False

    errors = validate_manifest_payload_v9_37(report, manifest)

    assert any("feature_store_created" in error for error in errors)


def _report() -> dict:
    flags = {
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_ml": True,
        "no_dataset_supervised": True,
        "no_labels": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "exchange_auth_used": False,
        "websocket_live_used": False,
        "network_used": False,
        "no_new_data_download": True,
        "no_destructive_cleanup": True,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }
    timeframe_reports = {
        timeframe: {
            "expected_rows": rows,
            "actual_rows": rows,
            "days_expected": 1827,
            "days_complete": 1827,
            "days_missing": 0,
            "coverage_status": "PASS",
            "quality_status": "PASS",
            "feature_available_ts_lte_decision_ts": True,
            "available_ts_lte_decision_ts": True,
            "forbidden_columns": [],
            "warmup_summary": {"warmup_rows": 60, "non_warmup_rows": rows - 60},
            "zero_trade_bucket_summary": {"zero_trade_rows": 0, "zero_trade_ratio": 0.0},
            "errors": [],
        }
        for timeframe, rows in EXPECTED_ROWS_BY_TIMEFRAME.items()
    }
    report = {
        "version": "V9.37",
        "source_version": "V9.36",
        "source_versions": {"source_version": "V9.36"},
        "status": "PASS",
        "direction": "ohlcv_aggtrades_5y_feature_store",
        "decision": "ohlcv_aggtrades_5y_feature_store_created_with_warnings",
        "target_window": {"start": "2021-05-05", "end": "2026-05-05", "days_expected": 1827},
        "timeframes": ["1m", "5m", "15m", "1h"],
        "feature_store_created": True,
        "features_created": True,
        "feature_store_paths": {},
        "row_counts": {timeframe: rows for timeframe, rows in EXPECTED_ROWS_BY_TIMEFRAME.items()},
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "feature_families": {},
        "timeframe_reports": timeframe_reports,
        "leakage_guard": {"status": "PASS", "rolling_windows_past_only": True},
        "forbidden_column_scan": {"status": "PASS", "forbidden_columns": [], "scanned_terms": ["future", "label", "target", "prediction", "model_score", "signal", "trading_signal", "order", "pnl", "sharpe", "drawdown", "equity_curve", "profit_factor", "backtest", "position_size", "strategy", "entry", "exit", "trade_decision"]},
        "quality_status": "PASS",
        "coverage_status": "target_5y_feature_window_complete",
        "next_recommendation": "V9.38 - OHLCV + AggTrades 5Y Feature Store Validation",
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": {},
        "safety_flags": flags,
    }
    return deepcopy(report)
