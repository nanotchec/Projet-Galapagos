from typing import Any, Dict

class SafetyAudit:
    def audit_v1_79_execution(self, 
                              guard_res: Dict[str, Any], 
                              request_status: Dict[str, Any], 
                              write_res: Dict[str, Any],
                              resp_summary: Dict[str, Any]) -> Dict[str, Any]:
        
        passed = True
        critical_issues = []
        
        if not guard_res.get("v1_78_state_validated"):
            passed = False
            critical_issues.append("Input state V1.78 not validated")
            
        if request_status.get("requests_executed_count", 0) > 10:
            passed = False
            critical_issues.append("Request limit exceeded (> 10)")
            
        if write_res.get("new_data_files_created"):
            passed = False
            critical_issues.append("Unauthorized data files created")
            
        if resp_summary.get("successful_response_count", 0) > 0:
            if not resp_summary.get("response_status_codes_all_present"):
                passed = False
                critical_issues.append("Successful responses missing HTTP status codes")
                
        return {
            "safety_audit_passed": passed,
            "critical_issues": critical_issues,
            "infrastructure_only_preserved": not write_res.get("new_data_files_created")
        }
