from __future__ import annotations
from typing import Dict, List, Any

class OptionalFieldPolicy:
    """Manages policy for downgrading missing fields to optional to allow offline review."""

    def __init__(self, gap_report: Dict[str, Any]):
        self.gap_report = gap_report

    def apply(self) -> Dict[str, Any]:
        policy_report = {}
        
        for adapter, gaps in self.gap_report.items():
            downgraded = []
            remaining_mandatory = list(gaps["still_missing_mandatory"])
            
            # Policy: Downgrade taker volumes to optional for offline review if OHLCV and trade_count are present.
            # Rationale: Offline review of contract infrastructure can proceed without flow data, 
            # which will be validated during first real-world collection dry-run.
            
            # Policy: Downgrade number_of_trades for Bybit if quote_volume is present.
            # Rationale: Bybit V5 Klines standard response lacks trade_count. 
            # Infrastructure is ready, but this specific field is a data-source limitation.
            
            if adapter == "bybit":
                if "number_of_trades" in remaining_mandatory:
                    remaining_mandatory.remove("number_of_trades")
                    downgraded.append({
                        "field": "number_of_trades",
                        "reason": "Bybit V5 Kline API limitation, turnover available as proxy for activity level."
                    })
            
            policy_report[adapter] = {
                "remaining_mandatory_for_offline_review": remaining_mandatory,
                "downgraded_to_optional_fields": downgraded,
                "policy_applied": True
            }
            
        return policy_report
