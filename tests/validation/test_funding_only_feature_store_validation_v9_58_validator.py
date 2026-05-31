from __future__ import annotations

from galapagos.features.funding_only_feature_store_validation_v9_58 import SAFETY_FLAGS
from galapagos.features.funding_only_feature_store_validation_v9_58_validation import validate_funding_only_feature_store_validation_report_v9_58


def test_v9_58_validator_accepts_validated_report():
    report = {
        "version": "V9.58",
        "decision": "funding_only_feature_store_validated_with_warnings",
        "feature_store_validated": True,
        "quality_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "dataset_created": False,
        "labels_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_funding_only_feature_store_validation_report_v9_58(report)["passed"] is True


def test_v9_58_validator_rejects_label_creation():
    report = {
        "version": "V9.58",
        "decision": "funding_only_feature_store_validated",
        "feature_store_validated": True,
        "quality_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "dataset_created": False,
        "labels_created": True,
        "network_used": False,
        "new_data_downloaded": False,
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_funding_only_feature_store_validation_report_v9_58(report)["passed"] is False
