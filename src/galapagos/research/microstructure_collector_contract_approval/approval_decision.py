from __future__ import annotations

class ApprovalDecisionEngine:
    def __init__(self, checklist_result: dict[str, Any]):
        self.checklist_result = checklist_result

    def compute_decision(self) -> dict[str, Any]:
        all_passed = self.checklist_result.get("all_criteria_met", False)
        
        # In V1.56, we can only reach OFFLINE_REVIEW ready, never REAL_COLLECTION ready.
        decision = "MICROSTRUCTURE_COLLECTOR_CONTRACT_READY_FOR_OFFLINE_REVIEW" if all_passed else "MICROSTRUCTURE_COLLECTOR_CONTRACT_PARTIAL"
        
        return {
            "decision": decision,
            "contract_ready_for_offline_review": all_passed,
            "real_collection_approved": False,
            "human_review_required_before_collection": True,
            "approval_decision_status": "PASSED" if all_passed else "FAILED"
        }
