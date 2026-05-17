from __future__ import annotations
import pytest
from galapagos.research.microstructure_collector_contract_approval.approval_decision import ApprovalDecisionEngine
from galapagos.research.microstructure_collector_contract_approval.network_safety_approval import NetworkSafetyVerifier

def test_approval_decision_requires_all_criteria():
    # Test that if not all criteria are met, decision is PARTIAL
    checklist_partial = {"all_criteria_met": False}
    engine = ApprovalDecisionEngine(checklist_partial)
    res = engine.compute_decision()
    assert res["decision"] == "MICROSTRUCTURE_COLLECTOR_CONTRACT_PARTIAL"
    assert res["contract_ready_for_offline_review"] is False

def test_approval_decision_ready_for_offline_review():
    # Test that if all criteria are met, decision is READY_FOR_OFFLINE_REVIEW
    checklist_passed = {"all_criteria_met": True}
    engine = ApprovalDecisionEngine(checklist_passed)
    res = engine.compute_decision()
    assert res["decision"] == "MICROSTRUCTURE_COLLECTOR_CONTRACT_READY_FOR_OFFLINE_REVIEW"
    assert res["contract_ready_for_offline_review"] is True
    assert res["real_collection_approved"] is False

def test_network_safety_guard():
    # Test that network safety verifier correctly identifies leaks
    metrics_unsafe = {
        "network_disabled": True,
        "external_api_called": True, # Leak!
        "external_data_downloaded": False
    }
    verifier = NetworkSafetyVerifier(metrics_unsafe)
    res = verifier.verify()
    assert res["status"] == "FAILED"
    assert res["network_safety_approved"] is False

    metrics_safe = {
        "network_disabled": True,
        "external_api_called": False,
        "external_data_downloaded": False
    }
    verifier = NetworkSafetyVerifier(metrics_safe)
    res = verifier.verify()
    assert res["status"] == "PASSED"
    assert res["network_safety_approved"] is True
