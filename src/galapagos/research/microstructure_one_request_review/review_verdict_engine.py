from typing import Any, Dict

class ReviewVerdictEngine:
    def compute_verdict(self, reviews: Dict[str, bool]) -> Dict[str, Any]:
        all_passed = all(reviews.values())
        
        if all_passed:
            return {
                "final_verdict": "MICROSTRUCTURE_ONE_REQUEST_PREFLIGHT_REVIEW_PASSED",
                "recommended_next_step": "prepare explicit human approval for tiny two-request preflight or keep one-request boundary",
                "next_allowed_phase": "human_approval_required_before_any_collection_expansion",
                "one_request_preflight_review_passed": True
            }
        
        # Check for specific safety issues
        if not reviews.get("request_limit_review_passed", True) or not reviews.get("no_strategy_linkage_review_passed", True):
             return {
                "final_verdict": "MICROSTRUCTURE_ONE_REQUEST_PREFLIGHT_REVIEW_BLOCKED_BY_SAFETY_ISSUE",
                "recommended_next_step": "investigate safety issue before any further network action",
                "next_allowed_phase": "safety_issue_investigation",
                "one_request_preflight_review_passed": False
            }

        return {
            "final_verdict": "MICROSTRUCTURE_ONE_REQUEST_PREFLIGHT_REVIEW_INCOMPLETE",
            "recommended_next_step": "fix one-request preflight reporting before any further network action",
            "next_allowed_phase": "one_request_preflight_reporting_hardening",
            "one_request_preflight_review_passed": False
        }
