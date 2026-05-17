# Intrabar Availability v1.18.2

Verdict: **INTRABAR_5M_PUBLIC_AVAILABLE**

## JSON Payload
```json
{
  "status": "checked",
  "results": [
    {
      "status": "available",
      "source": "binance",
      "symbol": "BTCUSDT",
      "timeframe": "5m",
      "max_rows_per_call": 1000,
      "requires_key": false,
      "notes": "Binance public endpoint responds successfully.",
      "recommended_for_v1_18": true
    },
    {
      "status": "available",
      "source": "bybit",
      "symbol": "BTCUSDT",
      "timeframe": "5m",
      "max_rows_per_call": 1000,
      "requires_key": false,
      "notes": "Bybit public endpoint responds successfully.",
      "recommended_for_v1_18": false
    }
  ]
}
```
