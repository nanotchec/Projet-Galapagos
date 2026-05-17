# Adapter Field Gap Analysis

## Results
```json
{
  "adapters": {
    "binance": {
      "covered_required_fields": [
        "close",
        "high",
        "low",
        "number_of_trades",
        "open",
        "quote_asset_volume",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "volume"
      ],
      "still_missing_mandatory": [],
      "still_missing_optional": []
    },
    "bybit": {
      "covered_required_fields": [
        "close",
        "high",
        "low",
        "open",
        "quote_asset_volume",
        "volume"
      ],
      "still_missing_mandatory": [
        "number_of_trades"
      ],
      "still_missing_optional": [
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume"
      ]
    }
  },
  "version": "V1.57",
  "previous_base": "V1.56.1"
}
```

