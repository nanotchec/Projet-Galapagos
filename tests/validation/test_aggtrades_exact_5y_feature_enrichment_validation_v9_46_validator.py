from __future__ import annotations

import copy

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import EXPECTED_TIMEFRAMES, FEATURE_COLUMNS
from galapagos.features.aggtrades_exact_5y_feature_enrichment_validation_v9_46 import FINDINGS, SAFETY_FLAGS
from galapagos.features.aggtrades_exact_5y_feature_enrichment_validation_v9_46_validation import validate_manifest_payload_v9_46, validate_report_payload_v9_46


def test_v9_46_validator_accepts_valid_report_payload():
    assert validate_report_payload_v9_46(_report()) == []


def test_v9_46_validator_rejects_feature_or_ml_creation():
    report = _report()
    report["features_created"] = True
    report["ml_executed"] = True
    report["safety_flags"]["no_ml"] = False

    errors = validate_report_payload_v9_46(report)

    assert any("features_created" in error for error in errors)
    assert any("ml_executed" in error for error in errors)
    assert any("no_ml" in error for error in errors)


def test_v9_46_manifest_rejects_zip_fingerprint_field():
    report = _report()
    manifest = {
        "version": "V9.46",
        "source_version": "V9.45",
        "decision": report["decision"],
        "feature_columns_count": report["feature_columns_count"],
        "safety_flags": report["safety_flags"],
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "zip_sha256": "forbidden",
    }

    errors = validate_manifest_payload_v9_46(manifest, report)

    assert any("ZIP fingerprint" in error for error in errors)


def _report():
    return {
        "version": "V9.46",
        "source_version": "V9.45",
        "decision": "aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings",
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "features_created": False,
        "feature_store_combined_created": False,
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
        "coverage_validation": {"status": "PASS"},
        "schema_validation": {"status": "PASS"},
        "quality_validation": {"status": "PASS"},
        "leakage_guard": {"status": "PASS"},
        "forbidden_column_scan": {"status": "PASS"},
    }
