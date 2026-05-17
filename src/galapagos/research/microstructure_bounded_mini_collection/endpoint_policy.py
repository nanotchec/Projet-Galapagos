from typing import Any, Dict

class EndpointPolicy:
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.source = "Binance"
        self.endpoint_type = "Public Unauthenticated"
        # Using a stable public endpoint: Trades or Klines
        self.url_template = "https://api.binance.com/api/v3/trades?symbol={symbol}&limit={limit}"
        
    def get_policy(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "endpoint_type": self.endpoint_type,
            "symbol": self.symbol,
            "url_template": self.url_template,
            "endpoint_allowed": True,
            "endpoint_authentication_required": False,
            "secrets_required": False,
            "authenticated_request_allowed": False
        }
