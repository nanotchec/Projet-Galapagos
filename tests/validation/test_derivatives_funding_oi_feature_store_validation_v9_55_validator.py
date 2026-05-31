from __future__ import annotations

from galapagos.features.derivatives_funding_oi_feature_store_validation_v9_55 import SAFETY_FLAGS
from galapagos.features.derivatives_funding_oi_feature_store_validation_v9_55_validation import validate_derivatives_funding_oi_feature_store_validation_report_v9_55


def test_v9_55_validator_accepts_success():
    report = {
        "version": "V9.55",
        "decision": "derivatives_feature_store_validated_with_warnings",
        "quality_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "feature_store_validated": True,
        "ml_executed": False,
        "dataset_created": False,
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_derivatives_funding_oi_feature_store_validation_report_v9_55(report)["passed"] is True


def test_v9_55_validator_rejects_ml_execution():
    report = {
        "version": "V9.55",
        "decision": "derivatives_feature_store_validated_with_warnings",
        "quality_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "feature_store_validated": True,
        "ml_executed": True,
        "dataset_created": False,
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_derivatives_funding_oi_feature_store_validation_report_v9_55(report)["passed"] is False
