from __future__ import annotations

from galapagos.features.derivatives_funding_oi_feature_store_v9_54 import SAFETY_FLAGS
from galapagos.features.derivatives_funding_oi_feature_store_v9_54_validation import validate_derivatives_funding_oi_feature_store_report_v9_54


def test_v9_54_validator_accepts_audit_lite_success():
    report = {
        "version": "V9.54",
        "decision": "derivatives_funding_feature_store_created",
        "quality_status": "PASS",
        "schema_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "open_interest_included": False,
        "feature_store_paths": {"1h": "missing-in-audit-lite.parquet"},
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_derivatives_funding_oi_feature_store_report_v9_54(report, mode="audit-lite")["passed"] is True


def test_v9_54_validator_rejects_leakage_failure_on_success():
    report = {
        "version": "V9.54",
        "decision": "derivatives_funding_feature_store_created",
        "quality_status": "PASS",
        "schema_status": "PASS",
        "leakage_guard": {"status": "FAIL"},
        "open_interest_included": False,
        "feature_store_paths": {},
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_derivatives_funding_oi_feature_store_report_v9_54(report, mode="audit-lite")["passed"] is False
