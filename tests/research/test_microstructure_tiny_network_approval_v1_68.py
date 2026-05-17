import pytest
from galapagos.research.microstructure_tiny_network_approval.input_guard import InputGuard
from galapagos.research.microstructure_tiny_network_approval.approval_gate import V167ProtocolReview, HumanApprovalGate
from galapagos.research.microstructure_tiny_network_approval.verdict_engine import AuthorizationVerdictEngine

def test_input_guard_pass():
    ig = InputGuard()
    summary = {
        "version": "V1.67",
        "controlled_collection_readiness_review_passed": True,
        "tiny_collection_protocol_defined": True,
        "human_approval_required_before_network": True,
        "human_approval_granted": False,
        "next_allowed_phase": "human_approval_required_for_tiny_network_collection_preflight",
        "network_enabled": False,
        "real_collection_approved": False,
        "requests_executed_count": 0
    }
    assert ig.validate(summary) is True

def test_input_guard_fail_approval():
    ig = InputGuard()
    summary = {
        "version": "V1.67",
        "human_approval_granted": True
    }
    assert ig.validate(summary) is False

def test_v167_protocol_review():
    review = V167ProtocolReview()
    summary = {"human_approval_granted": False}
    proto = {
        "tiny_collection_protocol_defined": True,
        "max_request_count": 1,
        "no_dataset_write": True
    }
    res = review.review(summary, proto)
    assert res["v1_67_protocol_review_passed"] is True

def test_human_approval_gate():
    gate = HumanApprovalGate()
    res = gate.define()
    assert res["human_approval_gate_ready"] is True
    assert res["human_approval_granted"] is False
    assert "approve" in res["required_approval_phrase"].lower()

def test_verdict_engine():
    engine = AuthorizationVerdictEngine()
    verdict = engine.get_verdict(True, True, True)
    assert verdict == "MICROSTRUCTURE_TINY_NETWORK_PREFLIGHT_APPROVAL_GATE_READY"
    
    next_p = engine.get_next_phase(True)
    assert next_p == "await_explicit_human_approval_for_tiny_network_preflight"
