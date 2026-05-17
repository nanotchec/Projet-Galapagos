from typing import Any, Dict

class InputGuard:
    def validate_v1_77_1_state(self, summary: Dict[str, Any], audit: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        if summary.get("final_verdict") != "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_REPORTING_INCOMPLETE":
            issues.append(f"Unexpected verdict: {summary.get('final_verdict')}")
            
        if audit.get("previous_status_reporting_incomplete") is not True:
            issues.append("Reporting must be marked as incomplete in audit")
            
        return {
            "v1_77_1_state_validated": len(issues) == 0,
            "issues": issues,
            "previous_status_reporting_incomplete": True
        }
