from __future__ import annotations

from copy import deepcopy

from galapagos.features.ohlcv_aggtrades_5y_feature_store_validation_v9_38 import build_manifest_v9_38
from galapagos.features.ohlcv_aggtrades_5y_feature_store_validation_v9_38_validation import (
    validate_manifest_payload_v9_38,
    validate_report_payload_v9_38,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_schemas import EXPECTED_ROWS_BY_TIMEFRAME, FEATURE_COLUMNS


def test_v9_38_validator_accepts_validated_with_warnings_payload() -> None:
    report = _report()
    manifest = build_manifest_v9_38(report)

    assert validate_report_payload_v9_38(report) == []
    assert validate_manifest_payload_v9_38(report, manifest) == []


def test_v9_38_validator_rejects_network_usage() -> None:
    report = _report()
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_38(report)

    assert any("network" in error for error in errors)


def test_v9_38_validator_rejects_dataset_creation() -> None:
    report = _report()
    report["dataset_created"] = True

    errors = validate_report_payload_v9_38(report)

    assert any("dataset" in error for error in errors)


def test_v9_38_validator_rejects_schema_failure() -> None:
    report = _report()
    report["schema_status"] = "FAIL"
    report["schema_validation"]["status"] = "FAIL"

    errors = validate_report_payload_v9_38(report)

    assert any("schema" in error for error in errors)


def test_v9_38_validator_rejects_leakage_guard_failure() -> None:
    report = _report()
    report["leakage_guard_status"] = "FAIL"
    report["leakage_guard"]["status"] = "FAIL"

    errors = validate_report_payload_v9_38(report)

    assert any("leakage" in error for error in errors)


def test_v9_38_manifest_mismatch_is_detected() -> None:
    report = _report()
    manifest = build_manifest_v9_38(report)
    manifest["features_full_modified"] = True

    errors = validate_manifest_payload_v9_38(report, manifest)

    assert any("features_full_modified" in error for error in errors)


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
            "complete_calendar_coverage": True,
            "quality_status": "PASS",
            "strict_schema_status": "PASS",
            "feature_available_ts_lte_decision_ts": True,
            "available_ts_lte_decision_ts": True,
            "rolling_windows_past_only_status": "PASS",
            "forbidden_columns": [],
            "warmup_summary": {"warmup_rows": 60, "non_warmup_rows": rows - 60},
            "zero_trade_bucket_summary": {"zero_trade_rows": 0, "zero_trade_ratio": 0.0, "zero_trade_bucket_blocking": False},
            "errors": [],
        }
        for timeframe, rows in EXPECTED_ROWS_BY_TIMEFRAME.items()
    }
    report = {
        "version": "V9.38",
        "source_version": "V9.37",
        "status": "PASS",
        "direction": "ohlcv_aggtrades_5y_feature_store_validation",
        "decision": "ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings",
        "target_window": {"start": "2021-05-05", "end": "2026-05-05", "days_expected": 1827},
        "timeframes": ["1m", "5m", "15m", "1h"],
        "actual_rows": {timeframe: rows for timeframe, rows in EXPECTED_ROWS_BY_TIMEFRAME.items()},
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "feature_store_validation": timeframe_reports,
        "coverage_validation": {"status": "target_5y_feature_window_complete"},
        "schema_validation": {"status": "PASS", "forbidden_scan": {"status": "PASS", "forbidden_columns": [], "scanned_terms": ["future", "label", "target", "prediction", "model_score", "signal", "trading_signal", "order", "pnl", "sharpe", "drawdown", "equity_curve", "profit_factor", "backtest", "position_size", "strategy", "entry", "exit", "trade_decision"]}},
        "quality_validation": {"status": "PASS"},
        "leakage_guard": {"status": "PASS", "rolling_windows_past_only": True},
        "zero_trade_bucket_validation": {"status": "PASS", "zero_trade_bucket_blocking": False},
        "aggtrades_feature_limitations": {"direct_aggtrades_full_scan_performed": False, "non_blocking_for_current_feature_store_validation": True, "blocking_for_next_dataset": False},
        "quality_status": "PASS",
        "coverage_status": "target_5y_feature_window_complete",
        "schema_status": "PASS",
        "leakage_guard_status": "PASS",
        "next_recommendation": "V9.39 - OHLCV + AggTrades 5Y Dataset",
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "features_full_modified": False,
        "findings": {},
        "safety_flags": flags,
    }
    return deepcopy(report)
