from typing import Dict, List, Any

class DryRunSchema:
    """Définitions théoriques des schémas pour le data contract dry-run."""
    
    @staticmethod
    def get_microstructure_schema() -> Dict[str, str]:
        return {
            "timestamp": "datetime64[ns]",
            "symbol": "string",
            "bid_price": "float64",
            "ask_price": "float64",
            "bid_size": "float64",
            "ask_size": "float64",
            "trade_price": "float64",
            "trade_size": "float64",
            "regime_label": "int32"
        }

    @staticmethod
    def get_mandatory_fields() -> List[str]:
        return ["timestamp", "symbol", "bid_price", "ask_price"]

    @staticmethod
    def get_partition_keys() -> List[str]:
        return ["symbol", "date"]
