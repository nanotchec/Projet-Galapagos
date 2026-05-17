from typing import Any, Dict

class PreflightVerdictEngine:
    def compute_verdict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        req_count = context.get("requests_executed_count", 0)
        success_count = context.get("success_count", 0)
        
        if context.get("blocked_by_auth"):
             return {
                "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_PREFLIGHT_BLOCKED_REQUIRES_AUTH_OR_SECRET",
                "recommended_next_step": "choose public unauthenticated endpoint or keep offline",
                "next_allowed_phase": "revise_two_request_endpoint_policy"
            }

        if context.get("blocked_by_guard"):
            return {
                "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_PREFLIGHT_BLOCKED_BY_SAFETY_GUARD",
                "recommended_next_step": "fix safety guard issue before any retry",
                "next_allowed_phase": "safety_guard_hardening"
            }

        if req_count > 0 and success_count > 0:
            return {
                "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
                "recommended_next_step": "review two-request preflight before any bounded mini-collection planning",
                "next_allowed_phase": "two_request_preflight_review_before_any_mini_collection_plan"
            }
        
        return {
            "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_PREFLIGHT_ATTEMPT_FAILED_SAFELY",
            "recommended_next_step": "review network failure before retrying any preflight",
            "next_allowed_phase": "retry_requires_new_human_review"
        }
