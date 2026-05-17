from typing import Any, Dict, List

class ReportingAudit:
    def perform_audit(self, v1_77_summary: Dict[str, Any], v1_77_client: Dict[str, Any]) -> Dict[str, Any]:
        prev_status_codes = v1_77_summary.get("response_status_codes", [])
        successful_count = v1_77_summary.get("successful_response_count", 0)
        
        # Check if codes are missing (None or empty while success > 0)
        status_reporting_incomplete = False
        if successful_count > 0:
            if not prev_status_codes or None in prev_status_codes:
                status_reporting_incomplete = True
                
        # Attempt recovery from client report if possible (unlikely in V1.77 but good practice)
        recovered_codes = v1_77_client.get("response_status_codes", [])
        
        fixed = False
        if status_reporting_incomplete:
             recovered_count = len(recovered_codes)
             if recovered_count == successful_count:
                  fixed = True
        
        return {
            "response_status_reporting_audit_performed": True,
            "previous_status_reporting_incomplete": status_reporting_incomplete,
            "response_status_reporting_fixed": fixed,
            "response_status_codes_available": fixed or (not status_reporting_incomplete),
            "response_status_codes": recovered_codes if fixed else (prev_status_codes if not status_reporting_incomplete else []),
            "response_status_codes_all_present": fixed or (not status_reporting_incomplete),
            "response_status_codes_none_present": False,
            "response_status_codes_missing_count": successful_count if status_reporting_incomplete and not fixed else 0
        }
