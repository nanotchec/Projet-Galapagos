# Intrabar Availability v1.18

Verdict: **INTRABAR_DRY_RUN_MOCKED**

## JSON Payload
```json
{
  "status": "checked",
  "results": [
    {
      "status": "dry_run_only",
      "source": "binance",
      "symbol": "BTCUSDT",
      "timeframe": "5m",
      "max_rows_per_call": 1000,
      "requires_key": false,
      "notes": "Dry run mode.",
      "recommended_for_v1_18": true
    },
    {
      "status": "dry_run_only",
      "source": "bybit",
      "symbol": "BTCUSDT",
      "timeframe": "5m",
      "max_rows_per_call": 1000,
      "requires_key": false,
      "notes": "Dry run mode.",
      "recommended_for_v1_18": false
    }
  ]
}
```
