from __future__ import annotations

from galapagos.research.refined_volnorm_research_decision_gate_v9_10 import FINDINGS_V9_10, SAFETY_FLAGS_V9_10, VERSION_V9_10
from galapagos.research.refined_volnorm_research_decision_gate_v9_10_validation import validate_report_payload_v9_10


def _payload() -> dict:
    return {
        "version": VERSION_V9_10,
        "status": "PASS",
        "decision_gate_type": "research_only",
        "research_decision": "backtest_not_justified_refine_labels_again",
        "findings": FINDINGS_V9_10,
        "safety": SAFETY_FLAGS_V9_10,
        "leakage_assessment": {"passed": True},
        "metric_forbidden_scan": {"passed": True},
        "next_step_recommendation": "Revoir les labels.",
    }


def test_validator_v9_10_accepts_valid_report_payload() -> None:
    assert validate_report_payload_v9_10(_payload()) == []


def test_validator_v9_10_rejects_strategy_validated_true() -> None:
    payload = _payload()
    payload["findings"] = {**FINDINGS_V9_10, "strategy_validated": True}
    assert "V9.10 findings mismatch" in validate_report_payload_v9_10(payload)


def test_validator_v9_10_rejects_safety_trading_true() -> None:
    payload = _payload()
    payload["safety"] = {**SAFETY_FLAGS_V9_10, "trading_enabled": True}
    assert "V9.10 safety mismatch" in validate_report_payload_v9_10(payload)
