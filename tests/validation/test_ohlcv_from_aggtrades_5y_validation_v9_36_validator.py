from __future__ import annotations

from copy import deepcopy

from galapagos.data.ohlcv_from_aggtrades_5y_validation_v9_36 import build_manifest_v9_36
from galapagos.data.ohlcv_from_aggtrades_5y_validation_v9_36_validation import (
    validate_manifest_payload_v9_36,
    validate_report_payload_v9_36,
)


def test_v9_36_validator_accepts_pass_with_non_blocking_warnings() -> None:
    report = _report()
    manifest = build_manifest_v9_36(report)

    assert validate_report_payload_v9_36(report) == []
    assert validate_manifest_payload_v9_36(report, manifest) == []


def test_v9_36_validator_rejects_network_usage() -> None:
    report = _report()
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_36(report)

    assert any("network" in error for error in errors)


def test_v9_36_validator_rejects_feature_store_creation() -> None:
    report = _report()
    report["combined_feature_store_created"] = True

    errors = validate_report_payload_v9_36(report)

    assert any("feature store" in error for error in errors)


def test_v9_36_validator_rejects_missing_timeframe_coverage() -> None:
    report = _report()
    report["coverage_validation"]["1m"]["days_missing"] = 1

    errors = validate_report_payload_v9_36(report)

    assert any("1m coverage" in error for error in errors)


def test_v9_36_validator_rejects_zero_trade_future_or_blocking_fill() -> None:
    report = _report()
    report["zero_trade_bucket_analysis"]["5m"]["causal_fill_uses_future_data"] = True

    errors = validate_report_payload_v9_36(report)

    assert any("5m zero-trade" in error for error in errors)


def test_v9_36_manifest_mismatch_is_detected() -> None:
    report = _report()
    manifest = build_manifest_v9_36(report)
    manifest["decision"] = "ohlcv_from_aggtrades_5y_validation_blocked_by_quality"

    errors = validate_manifest_payload_v9_36(report, manifest)

    assert any("decision" in error for error in errors)


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
        "no_feature_store": True,
        "no_combined_feature_store": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "exchange_auth_used": False,
        "websocket_live_used": False,
        "network_used": False,
        "no_new_data_download": True,
        "no_ingestion_executed": True,
        "no_data_deletion": True,
        "no_destructive_cleanup": True,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }
    coverage = {
        timeframe: {
            "quality_status": "PASS",
            "days_missing": 0,
            "complete_calendar_coverage": True,
        }
        for timeframe in ["1m", "5m", "15m", "1h"]
    }
    zero_trade = {
        timeframe: {
            "causal_fill_uses_future_data": False,
            "zero_trade_buckets_blocking": False,
        }
        for timeframe in ["1m", "5m", "15m", "1h"]
    }
    report = {
        "version": "V9.36",
        "source_version": "V9.35",
        "status": "PASS",
        "direction": "ohlcv_from_aggtrades_5y_coverage_validation",
        "target_window_start": "2021-05-05",
        "target_window_end": "2026-05-05",
        "timeframes_required": ["1m", "5m", "15m", "1h"],
        "decision": "ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings",
        "next_recommendation": "V9.37 - OHLCV + AggTrades 5Y Feature Store",
        "coverage_status": "target_5y_window_complete",
        "quality_status": "PASS",
        "parity_status": "PASS",
        "coverage_validation": coverage,
        "zero_trade_bucket_analysis": zero_trade,
        "feature_store_created": False,
        "combined_feature_store_created": False,
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
