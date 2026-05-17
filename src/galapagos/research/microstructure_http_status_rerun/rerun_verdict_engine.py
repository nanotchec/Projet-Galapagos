from typing import Any, Dict

class RerunVerdictEngine:
    def compute_verdict(self, audit_res: Dict[str, Any], net_summary: Dict[str, Any], resp_summary: Dict[str, Any]) -> Dict[str, Any]:
        success_count = net_summary.get("successful_requests", 0)
        total_requests = net_summary.get("total_requests", 0)
        
        if not audit_res.get("safety_audit_passed"):
            return {
                "final_verdict": "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_FAILED_SAFETY_AUDIT",
                "next_allowed_phase": "safety_incident_review",
                "bounded_http_status_rerun_executed": total_requests > 0
            }
            
        if success_count > 0:
            if resp_summary.get("response_status_codes_all_present") and resp_summary.get("response_status_codes_all_success"):
                return {
                    "final_verdict": "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_PASSED",
                    "next_allowed_phase": "bounded_http_status_rerun_review_before_any_data_write_proposal",
                    "bounded_http_status_rerun_executed": True
                }
            else:
                return {
                    "final_verdict": "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_REPORTING_INCOMPLETE",
                    "next_allowed_phase": "bounded_http_status_reporting_hardening",
                    "bounded_http_status_rerun_executed": True
                }
        
        if total_requests > 0:
            return {
                "final_verdict": "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_ATTEMPT_FAILED_SAFELY",
                "next_allowed_phase": "retry_requires_new_human_review",
                "bounded_http_status_rerun_executed": True
            }
            
        return {
            "final_verdict": "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_NOT_EXECUTED",
            "next_allowed_phase": "rerun_orchestration_fix",
            "bounded_http_status_rerun_executed": False
        }
