from typing import Any, Dict

class TinyCollectionProtocol:
    """
    Définit le protocole d'une future micro-collecte contrôlée.
    """
    def define(self) -> Dict[str, Any]:
        return {
            "tiny_collection_protocol_defined": True,
            "tiny_collection_protocol_only": True,
            "tiny_network_collection_executed": False,
            "target_symbol": "BTCUSDT",
            "timeframe": "1m",
            "max_request_count": 1,
            "max_records_preview": 10,
            "no_dataset_write": True,
            "no_parquet_csv_sqlite": True,
            "output_format": "REPORTS_JSON_MD_ONLY",
            "cleanup_required": True
        }

class HumanApprovalProtocol:
    """
    Définit le protocole d'approbation humaine.
    """
    def define(self) -> Dict[str, Any]:
        return {
            "human_approval_protocol_defined": True,
            "human_approval_required_before_network": True,
            "human_approval_granted": False,
            "approval_circuit": [
                "Technical review of security gates",
                "Explicit human consent via configuration flag",
                "Validation of limited budget/resource usage"
            ]
        }
