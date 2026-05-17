from typing import Any, Dict

class SafetyVerdictEngine:
    def compute_verdict(self, approval_granted: bool) -> Dict[str, Any]:
        if approval_granted:
            return {
                "final_verdict": "MICROSTRUCTURE_HUMAN_APPROVAL_INTAKE_VALIDATED_FOR_TINY_PREFLIGHT",
                "next_allowed_phase": "one_request_tiny_network_preflight_reports_only"
            }
        else:
            return {
                "final_verdict": "MICROSTRUCTURE_HUMAN_APPROVAL_INTAKE_PENDING",
                "next_allowed_phase": "provide_explicit_human_approval_phrase_for_one_request_preflight"
            }
