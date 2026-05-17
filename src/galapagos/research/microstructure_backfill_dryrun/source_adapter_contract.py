from __future__ import annotations


class SourceAdapterContract:
    """Theoretical specification for source adapters (Binance/Bybit). No network execution."""

    def __init__(self, required_fields_spec: dict, source_candidates: dict):
        self.required_fields = required_fields_spec.get("required_microstructure_fields", [])
        self.accepted_candidates = source_candidates.get("accepted_source_candidates", [])

    def analyze(self) -> dict:
        contract = {
            "status": "SOURCE_ADAPTER_CONTRACT_DEFINED_NO_NETWORK",
            "adapters": []
        }

        for candidate in self.accepted_candidates:
            if candidate == "binance_public_data_archives":
                contract["adapters"].append({
                    "name": "BinanceArchiveAdapter",
                    "theoretical_endpoint": "https://data.binance.vision/data/futures/um/daily/klines/",
                    "expected_fields": self.required_fields,
                    "supports_historical_bulk": True,
                    "network_execution_enabled": False
                })
            elif candidate == "bybit_v5_api":
                contract["adapters"].append({
                    "name": "BybitV5Adapter",
                    "theoretical_endpoint": "https://api.bybit.com/v5/market/kline",
                    "expected_fields": self.required_fields,
                    "supports_historical_bulk": False,
                    "network_execution_enabled": False
                })

        return contract
