from __future__ import annotations

from galapagos.research.derivatives_source_readiness_v9_52 import SAFETY_FLAGS
from galapagos.research.derivatives_source_readiness_v9_52_validation import validate_derivatives_source_readiness_report_v9_52


def test_v9_52_validator_accepts_success_report():
    report = {
        "version": "V9.52",
        "decision": "derivatives_source_readiness_funding_ready_oi_limited",
        "source_assessments": {"funding_rate": {}, "open_interest": {}},
        "network_used": False,
        "new_data_downloaded": False,
        "safety_flags": SAFETY_FLAGS,
    }

    assert validate_derivatives_source_readiness_report_v9_52(report)["passed"] is True


def test_v9_52_validator_rejects_network_use():
    flags = {**SAFETY_FLAGS, "network_used": True}
    report = {
        "version": "V9.52",
        "decision": "derivatives_source_readiness_funding_ready_oi_limited",
        "source_assessments": {"funding_rate": {}, "open_interest": {}},
        "network_used": True,
        "new_data_downloaded": False,
        "safety_flags": flags,
    }

    assert validate_derivatives_source_readiness_report_v9_52(report)["passed"] is False
