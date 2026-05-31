from __future__ import annotations

from galapagos.research.funding_tail_resolution_v9_56 import SAFETY_FLAGS
from galapagos.research.funding_tail_resolution_v9_56_validation import validate_funding_tail_resolution_report_v9_56


def test_v9_56_validator_accepts_closed_window_report():
    report = {
        "version": "V9.56",
        "decision": "funding_tail_unavailable_use_closed_common_window",
        "common_window_sufficient_for_feature_store": True,
        "actual_feature_window": {"end": "2026-04-30T16:00:00Z"},
        "full_target_window_quality": {"missing_intervals": 15},
        "network_used": True,
        "safety_flags": {**SAFETY_FLAGS, "network_used": True},
    }

    assert validate_funding_tail_resolution_report_v9_56(report)["passed"] is True


def test_v9_56_validator_rejects_private_endpoint_use():
    flags = {**SAFETY_FLAGS, "network_used": True, "private_endpoint_used": True}
    report = {
        "version": "V9.56",
        "decision": "funding_tail_unavailable_use_closed_common_window",
        "common_window_sufficient_for_feature_store": True,
        "actual_feature_window": {"end": "2026-04-30T16:00:00Z"},
        "full_target_window_quality": {"missing_intervals": 15},
        "network_used": True,
        "safety_flags": flags,
    }

    assert validate_funding_tail_resolution_report_v9_56(report)["passed"] is False
