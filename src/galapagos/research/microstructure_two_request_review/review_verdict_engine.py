from typing import Any, Dict

class ReviewVerdictEngine:
    def compute_verdict(self, review_results: Dict[str, bool]) -> Dict[str, Any]:
        all_passed = all(review_results.values())
        
        if all_passed:
            return {
                "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_PREFLIGHT_REVIEW_PASSED",
                "recommended_next_step": "prepare explicit human approval for bounded reports-only mini-collection or keep two-request boundary",
                "next_allowed_phase": "human_approval_required_before_any_bounded_mini_collection",
                "two_request_preflight_review_passed": True
            }
        
        # Check for safety issue (data writes or strategy linkage)
        safety_issue = not (review_results.get("no_data_write_review_passed", True) and 
                            review_results.get("no_strategy_linkage_review_passed", True))
        
        if safety_issue:
            return {
                "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_PREFLIGHT_REVIEW_BLOCKED_BY_SAFETY_ISSUE",
                "recommended_next_step": "investigate safety issue before any further network action",
                "next_allowed_phase": "safety_issue_investigation",
                "two_request_preflight_review_passed": False
            }
            
        return {
            "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_PREFLIGHT_REVIEW_INCOMPLETE",
            "recommended_next_step": "fix two-request preflight reporting before any further network action",
            "next_allowed_phase": "two_request_preflight_reporting_hardening",
            "two_request_preflight_review_passed": False
        }
