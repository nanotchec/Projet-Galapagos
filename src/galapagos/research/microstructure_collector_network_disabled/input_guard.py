from __future__ import annotations
from typing import Dict, Any


class CollectorInputGuard:
    """Validates input parameters for the microstructure collector."""

    @staticmethod
    def validate_inputs(inputs: Dict[str, Any]) -> bool:
        """Validates the input parameters."""
        required = ["source", "symbol", "timeframe", "start_ts", "end_ts"]
        if not all(k in inputs for k in required):
            return False
            
        if inputs["start_ts"] >= inputs["end_ts"]:
            return False
            
        if inputs["source"] not in ["binance", "bybit"]:
            return False
            
        return True
