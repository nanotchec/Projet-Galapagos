from __future__ import annotations

class RecommendationEngine:
    def __init__(self, decision: dict[str, Any]):
        self.decision = decision

    def get_recommendation(self) -> dict[str, Any]:
        ready = self.decision.get("contract_ready_for_offline_review", False)
        
        if ready:
            verdict = "MICROSTRUCTURE_COLLECTOR_CONTRACT_READY_FOR_OFFLINE_REVIEW"
            next_step = "perform human review of collector contract before any real collection"
        else:
            verdict = "MICROSTRUCTURE_COLLECTOR_CONTRACT_PARTIAL"
            next_step = "refine adapter field coverage before offline review"
            
        return {
            "final_verdict": verdict,
            "recommended_next_step": next_step,
            "human_review_required": True,
            "status": "PASSED" if ready else "FAILED"
        }
