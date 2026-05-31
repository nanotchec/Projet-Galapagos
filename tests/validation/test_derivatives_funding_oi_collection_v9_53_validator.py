from __future__ import annotations

from galapagos.data.derivatives_funding_oi_collection_v9_53 import SAFETY_FLAGS
from galapagos.data.derivatives_funding_oi_collection_v9_53_validation import validate_derivatives_funding_oi_collection_report_v9_53


def test_v9_53_validator_accepts_audit_lite_success():
    report = {
        "version": "V9.53",
        "decision": "funding_collection_complete_oi_not_ready",
        "funding": {"quality_status": "PASS", "missing_intervals": 0, "duplicate_funding_time": 0, "silver_path": "missing-in-audit-lite.parquet"},
        "oi": {"collected": False},
        "safety_flags": {**SAFETY_FLAGS, "network_used": True, "new_data_downloaded": True},
    }

    assert validate_derivatives_funding_oi_collection_report_v9_53(report, mode="audit-lite")["passed"] is True


def test_v9_53_validator_rejects_success_with_missing_intervals():
    report = {
        "version": "V9.53",
        "decision": "funding_collection_complete_oi_not_ready",
        "funding": {"quality_status": "PASS", "missing_intervals": 1, "duplicate_funding_time": 0},
        "oi": {"collected": False},
        "safety_flags": {**SAFETY_FLAGS, "network_used": True, "new_data_downloaded": True},
    }

    assert validate_derivatives_funding_oi_collection_report_v9_53(report, mode="audit-lite")["passed"] is False
