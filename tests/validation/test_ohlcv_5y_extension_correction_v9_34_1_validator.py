from __future__ import annotations

from copy import deepcopy

from galapagos.data.ohlcv_5y_extension_correction_v9_34_1 import build_manifest_v9_34_1
from galapagos.data.ohlcv_5y_extension_correction_v9_34_1_validation import (
    validate_manifest_payload_v9_34_1,
    validate_report_payload_v9_34_1,
)
from galapagos.data.ohlcv_5y_extension_v9_34 import SAFETY_FLAGS


def test_v9_34_1_validator_accepts_source_issue_payload() -> None:
    report = _report()
    manifest = build_manifest_v9_34_1(report)

    assert validate_report_payload_v9_34_1(report) == []
    assert validate_manifest_payload_v9_34_1(report, manifest) == []


def test_v9_34_1_validator_rejects_feature_store_creation() -> None:
    report = _report()
    report["feature_store_created"] = True
    report["combined_feature_store_created"] = True

    errors = validate_report_payload_v9_34_1(report)

    assert any("feature store" in error for error in errors)


def test_v9_34_1_validator_rejects_missing_bad_day_diagnostic() -> None:
    report = _report()
    report["bad_day_diagnostic"] = {"before": {}, "repair": {}}

    errors = validate_report_payload_v9_34_1(report)

    assert any("bad_day_diagnostic" in error for error in errors)


def test_v9_34_1_validator_rejects_redownload_without_network_flag() -> None:
    report = _report()
    report["network_used"] = False

    errors = validate_report_payload_v9_34_1(report)

    assert any("redownload requires network_used" in error for error in errors)


def test_v9_34_1_manifest_mismatch_is_detected() -> None:
    report = _report()
    manifest = build_manifest_v9_34_1(report)
    manifest["decision"] = "ohlcv_5y_extension_complete"

    errors = validate_manifest_payload_v9_34_1(report, manifest)

    assert any("decision" in error for error in errors)


def _report() -> dict:
    flags = dict(SAFETY_FLAGS)
    flags.update(
        {
            "network_used": True,
            "network_scope": "public_archive_read_only",
            "new_data_downloaded": False,
            "new_data_download_scope": "none",
            "ingestion_executed": False,
            "ingestion_scope": "none",
            "no_combined_feature_store": True,
        }
    )
    report = {
        "version": "V9.34.1",
        "source_version": "V9.34",
        "status": "FAIL",
        "direction": "ohlcv_5y_extension_correction",
        "target_window_start": "2021-05-05",
        "target_window_end": "2026-05-05",
        "decision": "ohlcv_5y_extension_failed_source_issue",
        "next_recommendation": "V9.35 - OHLCV From AggTrades Derivation",
        "bad_day_diagnostic": {
            "before": {"row_count": 1170, "expected_row_count": 1440},
            "repair": {"repair_status": "source_issue"},
            "after": {"row_count": 1170, "expected_row_count": 1440},
        },
        "redownload_attempted": True,
        "redownload_success": False,
        "diagnostic_after": {"missing_days_by_timeframe": {"1m": 589, "5m": 689, "15m": 689, "1h": 689}},
        "ohlcv_5y_ready": False,
        "collection_executed": False,
        "feature_store_created": False,
        "combined_feature_store_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": True,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "ohlcv_quality": {"quality_status": "FAIL", "coverage_status": "target_window_incomplete"},
        "repair_status": "source_issue",
        "findings": {},
        "safety_flags": flags,
    }
    return deepcopy(report)
