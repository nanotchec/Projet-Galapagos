import requests
import time
from typing import Any, Dict, List

class BoundedNetworkClient:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.responses: List[Dict[str, Any]] = []

    def execute_request(self, url: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            response = requests.get(url, timeout=self.timeout)
            duration = time.time() - start_time
            
            res_data = {
                "url": url,
                "status_code": response.status_code,
                "reason": response.reason,
                "duration_ms": int(duration * 1000),
                "headers": dict(response.headers),
                "success": response.status_code == 200,
                "content_length": len(response.content)
            }
            
            if res_data["success"]:
                try:
                    res_data["json_body"] = response.json()
                except:
                    res_data["json_body"] = None
                    res_data["error"] = "Invalid JSON"
            
            self.responses.append(res_data)
            return res_data
            
        except Exception as e:
            err_data = {
                "url": url,
                "success": False,
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
            self.responses.append(err_data)
            return err_data

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_requests": len(self.responses),
            "successful_requests": len([r for r in self.responses if r.get("success")]),
            "failed_requests": len([r for r in self.responses if not r.get("success")]),
            "response_status_codes": [r.get("status_code") for r in self.responses],
            "total_duration_ms": sum(r["duration_ms"] for r in self.responses),
            "total_size_bytes": sum(r.get("content_length", 0) for r in self.responses)
        }
