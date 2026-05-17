from typing import Any, Dict

class EndpointPolicy:
    def __init__(self):
        self.allowed_source = "Binance"
        self.allowed_endpoint = "https://api.binance.com/api/v3/klines"

    def get_policy(self, symbol: str) -> Dict[str, Any]:
        return {
            "source": self.allowed_source,
            "endpoint": self.allowed_endpoint,
            "symbol": symbol,
            "timeframe": "1m",
            "endpoint_authentication_required": False,
            "secrets_required": False,
            "endpoint_allowed": True,
            "authenticated_request_allowed": False
        }
