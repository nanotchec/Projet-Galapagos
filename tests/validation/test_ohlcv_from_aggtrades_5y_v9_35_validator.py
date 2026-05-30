from __future__ import annotations

from copy import deepcopy

from galapagos.data.ohlcv_from_aggtrades_5y_v9_35 import build_manifest_v9_35
from galapagos.data.ohlcv_from_aggtrades_5y_v9_35_validation import (
    validate_derived_schema_columns_v9_35,
    validate_manifest_payload_v9_35,
    validate_report_payload_v9_35,
)


def test_v9_35_validator_accepts_complete_with_warnings_payload() -> None:
    report = _report()
    manifest = build_manifest_v9_35(report)

    assert validate_report_payload_v9_35(report) == []
    assert validate_manifest_payload_v9_35(report, manifest) == []


def test_v9_35_validator_rejects_network_usage() -> None:
    report = _report()
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_35(report)

    assert any("network" in error for error in errors)


def test_v9_35_validator_rejects_combined_feature_store() -> None:
    report = _report()
    report["combined_feature_store_created"] = True

    errors = validate_report_payload_v9_35(report)

    assert any("feature store" in error for error in errors)


def test_v9_35_validator_rejects_complete_without_all_timeframes() -> None:
    report = _report()
    report["timeframes_produced"] = ["1m", "5m", "15m"]

    errors = validate_report_payload_v9_35(report)

    assert any("all four timeframes" in error for error in errors)


def test_v9_35_manifest_mismatch_is_detected() -> None:
    report = _report()
    manifest = build_manifest_v9_35(report)
    manifest["decision"] = "ohlcv_from_aggtrades_5y_derivation_partial"

    errors = validate_manifest_payload_v9_35(report, manifest)

    assert any("decision" in error for error in errors)


def test_v9_35_schema_validator_rejects_extra_or_missing_columns() -> None:
    errors = validate_derived_schema_columns_v9_35(["source", "venue", "unexpected"])

    assert any("missing derived OHLCV columns" in error for error in errors)
    assert any("unexpected derived OHLCV columns" in error for error in errors)


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
        "no_destructive_cleanup": True,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }
    timeframe_reports = [
        {"timeframe": "1m", "quality_status": "PASS", "days_missing": 0},
        {"timeframe": "5m", "quality_status": "PASS", "days_missing": 0},
        {"timeframe": "15m", "quality_status": "PASS", "days_missing": 0},
        {"timeframe": "1h", "quality_status": "PASS", "days_missing": 0},
    ]
    report = {
        "version": "V9.35",
        "source_version": "V9.34.1",
        "status": "PASS",
        "direction": "ohlcv_from_aggtrades_5y_derivation",
        "target_window_start": "2021-05-05",
        "target_window_end": "2026-05-05",
        "timeframes_required": ["1m", "5m", "15m", "1h"],
        "method": {"ohlcv_source_type": "derived_from_aggtrades", "network_used": False},
        "decision": "ohlcv_from_aggtrades_5y_derivation_complete_with_warnings",
        "next_recommendation": "V9.36 - OHLCV From AggTrades 5Y Coverage Validation",
        "quality_status": "PASS",
        "coverage_status": "target_5y_window_complete",
        "timeframes_produced": ["1m", "5m", "15m", "1h"],
        "row_counts": {"1m": 2630880, "5m": 526176, "15m": 175392, "1h": 43848},
        "timeframe_reports": timeframe_reports,
        "feature_store_created": False,
        "combined_feature_store_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": True,
        "findings": {},
        "safety_flags": flags,
    }
    return deepcopy(report)
