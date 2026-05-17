from typing import Dict, Any

class OfflineReviewDecision:
    """Makes the final decision for the V1.58 review gate."""
    
    def decide(self, checklist_passed: bool, risk_count: int) -> Dict[str, Any]:
        # Gate passes if checklist is OK and risks are identified/mitigated
        gate_passed = checklist_passed and risk_count > 0
        
        return {
            "offline_review_gate_passed": gate_passed,
            "next_allowed_phase": "controlled_preflight_planning" if gate_passed else "more_contract_refinement",
            "verdict": "MICROSTRUCTURE_OFFLINE_REVIEW_GATE_PASSED" if gate_passed else "MICROSTRUCTURE_OFFLINE_REVIEW_GATE_BLOCKED",
            "real_collection_approved": False, # ALWAYS FALSE in V1.58
            "human_review_required_before_collection": True
        }
