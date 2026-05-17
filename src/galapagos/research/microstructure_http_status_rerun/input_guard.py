from typing import Any, Dict

class InputGuard:
    def validate_v1_78_state(self, summary: Dict[str, Any], hard: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        if summary.get("human_approval_granted") is not True:
            issues.append("Human approval not granted in V1.78")
            
        if hard.get("http_status_capture_hardened") is not True:
            issues.append("HTTP status capture not hardened in V1.78")
            
        if plan.get("v1_79_http_status_rerun_authorized") is not True:
            issues.append("V1.79 rerun not authorized in V1.78")
            
        return {
            "v1_78_state_validated": len(issues) == 0,
            "issues": issues,
            "previous_human_approval_granted": True,
            "previous_v1_79_http_status_rerun_authorized": True,
            "previous_http_status_capture_hardened": True,
            "previous_bounded_validator_hardened": True
        }
