import requests
from typing import Any, Dict, Optional

class TinyNetworkClient:
    def __init__(self, one_request_guard: Any):
        self.guard = one_request_guard

    def fetch_data(self, url: str) -> Dict[str, Any]:
        if not self.guard.authorize_request():
            return {
                "success": False,
                "error": "One-request limit reached or unauthorized by guard",
                "status_code": None
            }

        try:
            # Short timeout, no retry as per requirements
            response = requests.get(url, timeout=10)
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "raw_response": response.json() if response.status_code == 200 else None,
                "response_size_bytes": len(response.content),
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "error": str(e),
                "raw_response": None,
                "response_size_bytes": 0
            }
