from __future__ import annotations
from typing import Dict, Any

class CoverageDecisionEngine:
    """Computes the final decision on whether the contract is ready for offline review."""

    def __init__(self, policy_report: Dict[str, Any], gap_report: Dict[str, Any]):
        self.policy_report = policy_report
        self.gap_report = gap_report

    def compute(self) -> Dict[str, Any]:
        ready = True
        reasons = []
        
        for adapter, res in self.policy_report.items():
            if res["remaining_mandatory_for_offline_review"]:
                ready = False
                reasons.append(f"{adapter} missing mandatory fields: {res['remaining_mandatory_for_offline_review']}")
        
        if ready:
            verdict = "MICROSTRUCTURE_FIELD_COVERAGE_READY_FOR_OFFLINE_REVIEW"
            next_step = "perform human offline review of collector contract before any real collection"
        else:
            verdict = "MICROSTRUCTURE_FIELD_COVERAGE_PARTIAL"
            next_step = "refine adapter field coverage before offline review"
            
        return {
            "verdict": verdict,
            "contract_ready_for_offline_review": ready,
            "real_collection_approved": False,
            "human_review_required_before_collection": True,
            "recommended_next_step": next_step,
            "blocking_reasons": reasons
        }
