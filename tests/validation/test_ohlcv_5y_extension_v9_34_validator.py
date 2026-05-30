from __future__ import annotations

from copy import deepcopy

from galapagos.data.ohlcv_5y_extension_v9_34 import build_manifest_v9_34
from galapagos.data.ohlcv_5y_extension_v9_34_validation import (
    validate_manifest_payload_v9_34,
    validate_report_payload_v9_34,
)


def test_v9_34_validator_accepts_complete_payload() -> None:
    report = _report()
    manifest = build_manifest_v9_34(report)

    assert validate_report_payload_v9_34(report) == []
    assert validate_manifest_payload_v9_34(report, manifest) == []


def test_v9_34_validator_rejects_private_source() -> None:
    report = _report()
    report["source"]["host"] = "api.binance.com"

    errors = validate_report_payload_v9_34(report)

    assert any("public archive" in error for error in errors)


def test_v9_34_validator_rejects_complete_decision_with_missing_days() -> None:
    report = _report()
    report["diagnostic_after"]["missing_days_by_timeframe"]["1m"] = 1

    errors = validate_report_payload_v9_34(report)

    assert any("zero missing days" in error for error in errors)


def test_v9_34_validator_rejects_labels_or_ml() -> None:
    report = _report()
    report["labels_created"] = True
    report["ml_executed"] = True

    errors = validate_report_payload_v9_34(report)

    assert any("labels" in error for error in errors)


def test_v9_34_manifest_mismatch_is_detected() -> None:
    report = _report()
    manifest = build_manifest_v9_34(report)
    manifest["decision"] = "ohlcv_5y_extension_partial"

    errors = validate_manifest_payload_v9_34(report, manifest)

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
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "exchange_auth_used": False,
        "websocket_live_used": False,
        "no_destructive_cleanup": True,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
        "network_used": True,
        "new_data_downloaded": True,
        "ingestion_executed": True,
    }
    report = {
        "version": "V9.34",
        "source_version": "V9.33",
        "status": "PASS",
        "direction": "ohlcv_5y_extension",
        "decision": "ohlcv_5y_extension_complete",
        "next_recommendation": "V9.35 - OHLCV + AggTrades 5Y Feature Store",
        "target_window_start": "2021-05-05",
        "target_window_end": "2026-05-05",
        "missing_window_start": "2021-05-05",
        "missing_window_end": "2023-03-24",
        "timeframes_required": ["1m", "5m", "15m", "1h"],
        "source": {"host": "data.binance.vision", "public_read_only": True},
        "diagnostic_after": {"missing_days_by_timeframe": {"1m": 0, "5m": 0, "15m": 0, "1h": 0}},
        "ohlcv_5y_ready": True,
        "collection_executed": True,
        "network_used": True,
        "new_data_downloaded": True,
        "ingestion_executed": True,
        "ohlcv_quality": {"quality_status": "PASS", "coverage_status": "target_window_complete"},
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": {},
        "safety_flags": flags,
    }
    return deepcopy(report)
