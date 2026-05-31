from __future__ import annotations

import copy

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45 import FINDINGS, SAFETY_FLAGS
from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import EXPECTED_TIMEFRAMES, FEATURE_COLUMNS
from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_validation import validate_manifest_payload_v9_45, validate_report_payload_v9_45


def test_v9_45_validator_accepts_valid_report_payload():
    assert validate_report_payload_v9_45(_report()) == []


def test_v9_45_validator_rejects_network_or_ml_execution():
    report = _report()
    report["network_used"] = True
    report["ml_executed"] = True
    report["safety_flags"]["network_used"] = True
    report["safety_flags"]["no_ml"] = False
    errors = validate_report_payload_v9_45(report)
    assert any("network_used" in error for error in errors)
    assert any("ml_executed" in error for error in errors)
    assert any("network_used" in error for error in errors)


def test_v9_45_manifest_rejects_zip_fingerprint_field():
    report = _report()
    manifest = {"version": "V9.45", "source_version": "V9.44", "decision": report["decision"], "feature_columns_count": report["feature_columns_count"], "safety_flags": report["safety_flags"], "zip_sha256": "forbidden"}
    errors = validate_manifest_payload_v9_45(manifest, report)
    assert any("ZIP fingerprint" in error for error in errors)


def _report():
    return {
        "version": "V9.45",
        "source_version": "V9.44",
        "source_aggtrades_validation_version": "V9.32",
        "decision": "aggtrades_exact_5y_feature_enrichment_created_with_warnings",
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "findings": copy.deepcopy(FINDINGS),
        "safety_flags": copy.deepcopy(SAFETY_FLAGS),
        "leakage_guard": {"status": "PASS"},
        "forbidden_column_scan": {"status": "PASS"},
    }
