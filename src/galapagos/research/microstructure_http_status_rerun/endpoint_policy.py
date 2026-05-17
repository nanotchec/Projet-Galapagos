from typing import Any, Dict

class EndpointPolicy:
    def __init__(self, symbol: str):
        self.symbol = symbol
        # Use Binance public Trades endpoint (non-authenticated)
        self.base_url = "https://api.binance.com/api/v3/trades"

    def get_policy(self) -> Dict[str, Any]:
        return {
            "endpoint_allowed": True,
            "endpoint_authentication_required": False,
            "authenticated_request_allowed": False,
            "secrets_required": False,
            "url_template": self.base_url + "?symbol={symbol}&limit={limit}",
            "symbol": self.symbol,
            "provider": "Binance",
            "access_type": "public_unauthenticated"
        }
