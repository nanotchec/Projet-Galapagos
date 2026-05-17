from typing import Any, Dict

class SafetyVerdictEngine:
    def compute_verdict(self, approved: bool, guard_passed: bool) -> Dict[str, Any]:
        if not guard_passed:
            return {
                "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_APPROVAL_BLOCKED_BY_INPUT_GUARD",
                "recommended_next_step": "fix input guard issues from V1.72 before any approval attempt",
                "next_allowed_phase": "microstructure_review_revalidation"
            }
            
        if not approved:
            return {
                "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_APPROVAL_INTAKE_PENDING",
                "recommended_next_step": "provide exact approval phrase only if you want to authorize V1.74 two-request network preflight",
                "next_allowed_phase": "provide_explicit_human_approval_phrase_for_two_request_preflight"
            }

        return {
            "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_APPROVAL_INTAKE_VALIDATED",
            "recommended_next_step": "execute at most two-request tiny network preflight in V1.74 with reports-only output",
            "next_allowed_phase": "two_request_tiny_network_preflight_reports_only"
        }
