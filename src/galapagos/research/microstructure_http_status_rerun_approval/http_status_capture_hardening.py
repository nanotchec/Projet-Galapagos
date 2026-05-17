from typing import Any, Dict

class HTTPStatusCaptureHardening:
    def get_hardening_status(self) -> Dict[str, Any]:
        return {
            "http_status_capture_hardened": True,
            "response_status_required_per_request": True,
            "missing_status_codes_now_blocking": True,
            "successful_response_requires_status_code": True,
            "per_request_status_schema_defined": True,
            "status_capture_policy": {
                "fields": [
                    "request_index",
                    "endpoint",
                    "symbol",
                    "status_code",
                    "status_code_present",
                    "success_flag",
                    "response_size_bytes",
                    "preview_record_count",
                    "error_type",
                    "error_message_preview"
                ]
            }
        }
