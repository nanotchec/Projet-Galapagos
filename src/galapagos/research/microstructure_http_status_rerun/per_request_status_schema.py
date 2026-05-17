from typing import Any, Dict, List

class PerRequestStatusSchema:
    def format_records(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records = []
        for r in responses:
            records.append({
                "request_index": r.get("request_index"),
                "status_code": r.get("status_code"),
                "status_code_present": r.get("status_code_present"),
                "success_flag": r.get("success_flag"),
                "response_size_bytes": r.get("response_size_bytes"),
                "error_type": r.get("error_type"),
                "error_message_preview": r.get("error_message_preview")
            })
        return records
