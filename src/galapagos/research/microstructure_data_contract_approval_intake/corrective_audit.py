from typing import Any, Dict

class CorrectiveAudit:
    def __init__(self):
        self.version = "V1.81.1"
        self.corrective_for = "V1.81"

    def audit_v1_81_1_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        # Check for scope drift
        if state.get("v1_82_execution_attempted") is not False:
            issues.append("Scope drift: V1.82 execution attempted")
        if state.get("data_contract_dryrun_executed") is not False:
            issues.append("Scope drift: Data contract dry-run executed")
        if state.get("ml_signal_validation_executed") is not False:
            issues.append("Activity violation: ML signal validation executed")
            
        return {
            "corrective_audit_passed": len(issues) == 0,
            "issues": issues,
            "version": self.version,
            "corrective_for_version": self.corrective_for,
            "scope_drift_detected": len(issues) > 0,
            "v1_82_execution_attempted": state.get("v1_82_execution_attempted", False),
            "data_contract_dryrun_executed": state.get("data_contract_dryrun_executed", False)
        }
