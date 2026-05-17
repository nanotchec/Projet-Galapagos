import pytest
from galapagos.research.microstructure_collector_offline_review.input_guard import OfflineReviewInputGuard
from galapagos.research.microstructure_collector_offline_review.review_checklist import OfflineReviewChecklist
from galapagos.research.microstructure_collector_offline_review.safety_audit import OfflineReviewSafetyAudit

def test_input_guard_validates_v1572():
    guard = OfflineReviewInputGuard()
    valid_data = {
        "field_coverage_summary": {
            "version": "V1.57.2",
            "real_collection_approved": False,
            "contract_ready_for_offline_review": True
        },
        "contract_approval_summary": {
            "version": "V1.56.1"
        }
    }
    assert guard.validate(valid_data) is True

def test_input_guard_rejects_wrong_version():
    guard = OfflineReviewInputGuard()
    invalid_data = {
        "field_coverage_summary": {
            "version": "V1.57.1"
        }
    }
    assert guard.validate(invalid_data) is False
    assert "Invalid field coverage version" in guard.issues[0]

def test_safety_audit_is_strictly_infrastructure_only():
    audit = OfflineReviewSafetyAudit()
    report = audit.audit()
    assert report["network_disabled"] is True
    assert report["real_collection_approved"] is False
    assert report["requests_executed_count"] == 0
    assert report["evidence_classification"] == "INFRASTRUCTURE_ONLY"

def test_checklist_verifies_real_collection_flag():
    checklist = OfflineReviewChecklist()
    data = {
        "field_coverage_summary": {
            "real_collection_approved": True
        }
    }
    results = checklist.verify(data)
    assert results["real_collection_not_approved"] is False
