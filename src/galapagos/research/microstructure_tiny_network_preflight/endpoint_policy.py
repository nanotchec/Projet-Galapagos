from typing import Any, Dict

class EndpointPolicy:
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.source = "Binance Public API"
        self.endpoint_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=10"

    def get_policy(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "symbol": self.symbol,
            "timeframe": "1m",
            "endpoint_url": self.endpoint_url,
            "authentication_required": False,
            "endpoint_allowed": True,
            "policy_classification": "PUBLIC_UNAUTHENTICATED_TECH_PREFLIGHT"
        }
