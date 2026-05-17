import time
import requests
from typing import Any, Dict, List

class HTTPStatusNetworkClient:
    def __init__(self):
        self.responses = []

    def execute_request(self, url: str):
        start_time = time.time()
        try:
            # NO TIMEOUT SPECIFIED TO BE ROBUST IN MINI COLLECTION
            resp = requests.get(url)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Capture mandatory status info
            res_obj = {
                "request_index": len(self.responses),
                "endpoint": url,
                "status_code": resp.status_code,
                "status_code_present": True,
                "success_flag": resp.status_code == 200,
                "response_size_bytes": len(resp.content),
                "duration_ms": duration_ms,
                "content": resp.json() if resp.status_code == 200 else None,
                "error_type": None,
                "error_message_preview": None
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            res_obj = {
                "request_index": len(self.responses),
                "endpoint": url,
                "status_code": None,
                "status_code_present": False,
                "success_flag": False,
                "response_size_bytes": 0,
                "duration_ms": duration_ms,
                "content": None,
                "error_type": type(e).__name__,
                "error_message_preview": str(e)[:100]
            }
            
        self.responses.append(res_obj)
        return res_obj

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_requests": len(self.responses),
            "successful_requests": len([r for r in self.responses if r.get("success_flag")]),
            "failed_requests": len([r for r in self.responses if not r.get("success_flag")]),
            "response_status_codes": [r.get("status_code") for r in self.responses],
            "total_duration_ms": sum(r["duration_ms"] for r in self.responses),
            "total_size_bytes": sum(r.get("response_size_bytes", 0) for r in self.responses)
        }
