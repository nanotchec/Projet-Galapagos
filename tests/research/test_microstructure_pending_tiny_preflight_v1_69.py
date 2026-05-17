import pytest
from galapagos.research.microstructure_pending_tiny_preflight.input_guard import InputGuard
from galapagos.research.microstructure_pending_tiny_preflight.approval_logic import ApprovalPhraseGate, PendingApprovalMode
from galapagos.research.microstructure_pending_tiny_preflight.runner_logic import BlockedRunner
from galapagos.research.microstructure_pending_tiny_preflight.verdict_engine import VerdictEngine

def test_input_guard_pass():
    ig = InputGuard()
    summary = {
        "version": "V1.68",
        "human_approval_gate_ready": True,
        "human_approval_required_before_network": True,
        "human_approval_granted": False,
        "required_approval_phrase": "I explicitly approve...",
        "next_allowed_phase": "await_explicit_human_approval_for_tiny_network_preflight",
        "network_enabled": False,
        "real_collection_approved": False,
        "requests_executed_count": 0
    }
    assert ig.validate(summary) is True

def test_approval_phrase_gate_blocked():
    gate = ApprovalPhraseGate()
    # En V1.69, on ne fournit pas de phrase
    res = gate.check_approval("Required Phrase", None)
    assert res["approval_phrase_validated"] is False
    assert res["approval_phrase_not_provided"] is True

def test_blocked_runner():
    runner = BlockedRunner()
    res = runner.run_dry(False) # Pas d'approbation
    assert res["tiny_network_preflight_runner_blocked_without_approval"] is True
    assert res["tiny_network_collection_executed"] is False

def test_verdict_engine():
    engine = VerdictEngine()
    verdict = engine.get_verdict(True, True, True)
    assert verdict == "MICROSTRUCTURE_TINY_NETWORK_PREFLIGHT_COMMAND_PREPARED_PENDING_APPROVAL"
    
    next_p = engine.get_next_phase(True)
    assert next_p == "provide_explicit_human_approval_phrase_for_one_request_preflight"
