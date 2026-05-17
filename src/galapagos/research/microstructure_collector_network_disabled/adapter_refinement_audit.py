from __future__ import annotations
from typing import Dict, Any


class AdapterRefinementAudit:
    """Audits the refinement status of source adapters (V1.55)."""

    @staticmethod
    def audit_adapter(source: str) -> Dict[str, Any]:
        """Returns the refinement audit for a specific adapter."""
        if source == "binance":
            return {
                "source": "binance",
                "status": "REFINED_STUB",
                "mapped_fields": [
                    "open", "high", "low", "close", "volume", 
                    "quote_volume", "trade_count", 
                    "taker_buy_base_volume", "taker_buy_quote_volume"
                ],
                "missing_fields": [],
                "timestamp_precision": "ms",
                "causality_policy": "STRICT_CLOSE_TIME"
            }
        elif source == "bybit":
            return {
                "source": "bybit",
                "status": "PARTIAL_REFINED_STUB",
                "mapped_fields": [
                    "open", "high", "low", "close", "volume", "quote_volume"
                ],
                "missing_fields": [
                    "trade_count", "taker_buy_base_volume", "taker_buy_quote_volume"
                ],
                "timestamp_precision": "ms",
                "causality_policy": "ESTIMATED_FROM_TIMEFRAME"
            }
        return {"source": source, "status": "UNKNOWN"}
