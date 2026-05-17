from __future__ import annotations
from typing import Dict, List, Any

class RequiredFieldClassifier:
    """Classifies required fields from V1.52 based on their availability and criticality."""
    
    # Mapping from V1.52 names (without _5m) to V1.55 internal names
    FIELD_ALIAS_MAP = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "quote_asset_volume": "quote_volume",
        "number_of_trades": "trade_count",
        "taker_buy_base_asset_volume": "taker_buy_base_volume",
        "taker_buy_quote_asset_volume": "taker_buy_quote_volume"
    }

    def __init__(self, v152_spec: List[str]):
        self.v152_spec = [f.replace("_5m", "") for f in v152_spec]

    def classify(self) -> Dict[str, List[str]]:
        mandatory = []
        optional_collection = []
        unavailable = []
        
        for field in self.v152_spec:
            if field in ["open", "high", "low", "close", "volume"]:
                mandatory.append(field)
            elif field in ["quote_asset_volume", "number_of_trades"]:
                # High priority for microstructure but might be source dependent
                mandatory.append(field)
            elif field in ["taker_buy_base_asset_volume", "taker_buy_quote_asset_volume"]:
                # Crucial for flow analysis but often missing in standard klines
                optional_collection.append(field)
            else:
                unavailable.append(field)
        
        return {
            "mandatory_for_offline_review": mandatory,
            "optional_for_real_collection": optional_collection,
            "unavailable_until_real_source_metadata": unavailable,
            "field_alias_map": self.FIELD_ALIAS_MAP
        }
