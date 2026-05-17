"""Required field specification for Microstructure Data Enrichment Spec (V1.52)."""

class RequiredFieldSpec:
    def analyze(self):
        return {
            "status": "COMPLETED",
            "required_microstructure_fields": [
                "open_5m", "high_5m", "low_5m", "close_5m", "volume_5m",
                "quote_asset_volume_5m", "number_of_trades_5m",
                "taker_buy_base_asset_volume_5m", "taker_buy_quote_asset_volume_5m"
            ],
            "optional_microstructure_fields": [
                "bid_ask_spread_proxy", "order_book_imbalance_proxy"
            ],
            "field_definitions": {
                "taker_buy_base_asset_volume_5m": "Volume of base asset bought by market takers in 5m window",
                "number_of_trades_5m": "Total count of trades in 5m window"
            }
        }
