from typing import Any, Dict

class MiniCollectionVerdictEngine:
    def compute_verdict(self, 
                       safety_audit_res: Dict[str, Any],
                       network_summary: Dict[str, Any]) -> Dict[str, Any]:
        
        if not safety_audit_res.get("safety_audit_passed"):
            return {
                "final_verdict": "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_BLOCKED_BY_SAFETY_GUARD",
                "recommended_next_step": "fix safety guard issue before any retry",
                "next_allowed_phase": "safety_guard_hardening",
                "bounded_mini_collection_executed": network_summary.get("total_requests", 0) > 0
            }
            
        if network_summary.get("successful_requests", 0) > 0:
            return {
                "final_verdict": "MICROSTRUCTURE_BOUNDED_REPORTS_ONLY_MINI_COLLECTION_PASSED",
                "recommended_next_step": "review bounded mini-collection before any data-write or dataset proposal",
                "next_allowed_phase": "bounded_mini_collection_review_before_any_data_write_proposal",
                "bounded_mini_collection_executed": True
            }
            
        return {
            "final_verdict": "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_ATTEMPT_FAILED_SAFELY",
            "recommended_next_step": "review network failure before retrying any bounded mini-collection",
            "next_allowed_phase": "retry_requires_new_human_review",
            "bounded_mini_collection_executed": network_summary.get("total_requests", 0) > 0
        }
