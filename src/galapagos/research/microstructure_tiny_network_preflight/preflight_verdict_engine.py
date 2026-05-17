from typing import Any, Dict

class PreflightVerdictEngine:
    def compute_verdict(self, client_res: Dict[str, Any], guard_passed: bool) -> Dict[str, Any]:
        if not guard_passed:
            return {
                "final_verdict": "MICROSTRUCTURE_ONE_REQUEST_TINY_NETWORK_PREFLIGHT_BLOCKED_BY_SAFETY_GUARD",
                "recommended_next_step": "fix safety guard issue before any retry",
                "next_allowed_phase": "safety_guard_hardening"
            }
        
        if not client_res.get("success"):
            return {
                "final_verdict": "MICROSTRUCTURE_ONE_REQUEST_TINY_NETWORK_PREFLIGHT_ATTEMPT_FAILED_SAFELY",
                "recommended_next_step": "review network failure before retrying any preflight",
                "next_allowed_phase": "retry_requires_new_human_review"
            }

        return {
            "final_verdict": "MICROSTRUCTURE_ONE_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
            "recommended_next_step": "review one-request network preflight report before any further collection",
            "next_allowed_phase": "one_request_preflight_review_before_any_collection_expansion"
        }
