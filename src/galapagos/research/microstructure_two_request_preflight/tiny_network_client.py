import requests
from typing import Any, Dict, List, Optional

class TinyNetworkClient:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_klines(self, url: str, symbol: str, limit: int = 10) -> Dict[str, Any]:
        params = {
            "symbol": symbol,
            "interval": "1m",
            "limit": limit
        }
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "size_bytes": len(response.content),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0,
                "data": [],
                "size_bytes": 0,
                "error": str(e)
            }
