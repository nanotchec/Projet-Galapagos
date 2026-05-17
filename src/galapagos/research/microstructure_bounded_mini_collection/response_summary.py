from typing import Any, Dict, List

class ResponseSummary:
    def summarize(self, network_summary: Dict[str, Any], preview_res: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "successful_response_count": network_summary["successful_requests"],
            "failed_response_count": network_summary["failed_requests"],
            "response_status_codes": network_summary.get("response_status_codes", []),
            "response_size_bytes_total": network_summary["total_size_bytes"],
            "records_preview_count_total": preview_res["records_preview_count_total"],
            "response_summary_created": True,
            "response_schema_consistent": True if preview_res["records_preview_count_total"] > 0 else False
        }
