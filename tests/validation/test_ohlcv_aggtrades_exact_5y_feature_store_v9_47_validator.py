from __future__ import annotations

import copy

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47 import FINDINGS, SAFETY_FLAGS
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import EXPECTED_TIMEFRAMES, FEATURE_COLUMNS
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_validation import validate_manifest_payload_v9_47, validate_report_payload_v9_47


def test_v9_47_validator_accepts_valid_report_payload():
    assert validate_report_payload_v9_47(_report()) == []


def test_v9_47_validator_rejects_dataset_or_ml_creation():
    report = _report()
    report["dataset_created"] = True
    report["ml_executed"] = True
    report["safety_flags"]["no_ml"] = False

    errors = validate_report_payload_v9_47(report)

    assert any("dataset_created" in error for error in errors)
    assert any("ml_executed" in error for error in errors)
    assert any("no_ml" in error for error in errors)


def test_v9_47_manifest_rejects_zip_fingerprint_field():
    report = _report()
    manifest = {
        "version": "V9.47",
        "source_version": "V9.46",
        "decision": report["decision"],
        "combined_feature_columns_count": report["combined_feature_columns_count"],
        "safety_flags": report["safety_flags"],
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "zip_sha256": "forbidden",
    }

    errors = validate_manifest_payload_v9_47(manifest, report)

    assert any("ZIP fingerprint" in error for error in errors)


def _report():
    return {
        "version": "V9.47",
        "source_version": "V9.46",
        "decision": "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings",
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "combined_feature_columns_count": len(FEATURE_COLUMNS),
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": copy.deepcopy(FINDINGS),
        "safety_flags": copy.deepcopy(SAFETY_FLAGS),
        "leakage_guard": {"status": "PASS"},
        "forbidden_column_scan": {"status": "PASS"},
    }
