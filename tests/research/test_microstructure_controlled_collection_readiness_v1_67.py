import pytest
from galapagos.research.microstructure_controlled_collection_readiness.input_guard import InputGuard
from galapagos.research.microstructure_controlled_collection_readiness.readiness_review import ReadinessReview, NetworkActivationRiskAudit
from galapagos.research.microstructure_controlled_collection_readiness.tiny_collection_protocol import TinyCollectionProtocol, HumanApprovalProtocol
from galapagos.research.microstructure_controlled_collection_readiness.verdict_engine import ReadinessVerdictEngine

def test_input_guard_pass():
    ig = InputGuard()
    summary = {
        "version": "V1.66",
        "preflight_skeleton_fixture_execution_passed": True,
        "controlled_collection_readiness_plan_created": True,
        "next_allowed_phase": "controlled_collection_readiness_review",
        "network_enabled": False,
        "real_collection_approved": False,
        "requests_executed_count": 0
    }
    assert ig.validate(summary) is True

def test_input_guard_fail_version():
    ig = InputGuard()
    summary = {"version": "V1.65"}
    assert ig.validate(summary) is False

def test_readiness_review_audit():
    rr = ReadinessReview()
    plan = {
        "mandatory_checks_before_collection": [
            "Secrets audit (no API keys in code)",
            "Explicit human approval required",
            "Network disabled by default policy",
            "Tiny sample collection first (1 record)",
            "No data directory writes until review",
            "Rollback/Cleanup plan validation",
            "Audit logs verification"
        ]
    }
    res = rr.audit(plan)
    assert res["controlled_collection_readiness_review_passed"] is True

def test_risk_audit():
    audit = NetworkActivationRiskAudit()
    res = audit.audit()
    assert res["network_activation_risk_audit_completed"] is True
    assert len(res["network_activation_risks"]) > 0
    assert res["network_enabled"] is False

def test_verdict_engine():
    engine = ReadinessVerdictEngine()
    verdict = engine.get_verdict(True, True, True)
    assert verdict == "MICROSTRUCTURE_CONTROLLED_COLLECTION_READINESS_REVIEW_PASSED"
    
    next_p = engine.get_next_phase(True)
    assert next_p == "human_approval_required_for_tiny_network_collection_preflight"
