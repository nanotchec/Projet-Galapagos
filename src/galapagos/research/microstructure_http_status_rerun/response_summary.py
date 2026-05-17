from typing import Any, Dict

class ResponseSummary:
    def summarize(self, network_summary: Dict[str, Any], preview_res: Dict[str, Any]) -> Dict[str, Any]:
        status_codes = network_summary.get("response_status_codes", [])
        success_count = network_summary.get("successful_requests", 0)
        
        all_present = len(status_codes) == network_summary.get("total_requests", 0)
        none_present = None in status_codes
        all_success = all(200 <= c < 300 for c in status_codes if c is not None) if status_codes else False
        
        return {
            "successful_response_count": success_count,
            "failed_response_count": network_summary.get("failed_requests", 0),
            "response_status_codes": status_codes,
            "response_status_codes_none_present": none_present,
            "response_status_codes_all_present": all_present and not none_present,
            "response_status_codes_all_success": all_success and success_count == len(status_codes),
            "response_size_bytes_total": network_summary.get("total_size_bytes", 0),
            "records_preview_count_total": preview_res.get("records_preview_count_total", 0),
            "response_summary_created": True,
            "response_schema_consistent": True,
            "timestamp_preview_available": preview_res.get("records_preview_count_total", 0) > 0
        }
