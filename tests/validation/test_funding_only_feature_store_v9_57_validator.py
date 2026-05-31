from __future__ import annotations

from galapagos.features.funding_only_feature_store_v9_57 import SAFETY_FLAGS
from galapagos.features.funding_only_feature_store_v9_57_validation import validate_funding_only_feature_store_report_v9_57


def test_v9_57_validator_accepts_created_report():
    report = {
        "version": "V9.57",
        "decision": "funding_only_feature_store_created_with_warnings",
        "feature_store_created": True,
        "quality_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "feature_store_paths": {"1m": "a", "5m": "b", "15m": "c", "1h": "d"},
        "dataset_created": False,
        "labels_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_funding_only_feature_store_report_v9_57(report)["passed"] is True


def test_v9_57_validator_rejects_network_use():
    flags = {**SAFETY_FLAGS, "network_used": True}
    report = {
        "version": "V9.57",
        "decision": "funding_only_feature_store_created",
        "feature_store_created": True,
        "quality_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "feature_store_paths": {"1m": "a", "5m": "b", "15m": "c", "1h": "d"},
        "dataset_created": False,
        "labels_created": False,
        "network_used": True,
        "new_data_downloaded": False,
        "safety_flags": flags,
    }

    assert validate_funding_only_feature_store_report_v9_57(report)["passed"] is False
