# Microstructure Request Builder V1 54

```json
{
  "version": "V1.54",
  "request_plan": {
    "config": {
      "version": "V1.54",
      "source": "binance",
      "symbol": "BTCUSDT",
      "timeframe": "1m",
      "start_ts": 1704067200000,
      "end_ts": 1704153600000,
      "dry_run_only": true,
      "network_disabled": true,
      "max_requests": 100
    },
    "requests": [
      {
        "source": "binance",
        "method": "GET",
        "endpoint": "/api/v3/klines",
        "params": {
          "symbol": "BTCUSDT",
          "interval": "1m",
          "startTime": 1704067200000,
          "endTime": 1704127200000,
          "limit": 1000
        }
      },
      {
        "source": "binance",
        "method": "GET",
        "endpoint": "/api/v3/klines",
        "params": {
          "symbol": "BTCUSDT",
          "interval": "1m",
          "startTime": 1704127200001,
          "endTime": 1704153600000,
          "limit": 1000
        }
      }
    ],
    "total_expected_rows": 1440,
    "estimated_files_count": 2
  },
  "requests_built_count": 2
}
```
