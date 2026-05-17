from typing import Any, Dict

class SafetyVerdictEngine:
    def compute_verdict(self, 
                       guard_res: Dict[str, Any],
                       approval_res: Dict[str, Any]) -> Dict[str, Any]:
        
        if not guard_res.get("v1_77_1_state_validated"):
            return {
                "final_verdict": "MICROSTRUCTURE_HTTP_STATUS_RERUN_BLOCKED_BY_INPUT_GUARD",
                "next_allowed_phase": "input_state_correction"
            }
            
        if not approval_res.get("approval_phrase_validated"):
            return {
                "final_verdict": "MICROSTRUCTURE_HTTP_STATUS_RERUN_BLOCKED_BY_APPROVAL_VALIDATOR",
                "next_allowed_phase": "approval_phrase_retry"
            }
            
        return {
            "final_verdict": "MICROSTRUCTURE_HTTP_STATUS_CAPTURE_HARDENED_AND_RERUN_APPROVED",
            "next_allowed_phase": "bounded_http_status_rerun_reports_only"
        }
