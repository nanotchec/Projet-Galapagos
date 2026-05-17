# Local Fixture Preflight Run

Simulates the collection pipeline using fixtures.

- **Version**: V1.60
- **Status**: PASSED

```json
{
  "status": "PASSED",
  "local_fixture_preflight_status": "COMPLETED",
  "simulation_log": [
    "Processing binance_klines_fixture_v1_55.json: LOAD -> NORMALIZE -> VALIDATE_TIMESTAMPS -> GENERATE_MANIFEST_PREVIEW",
    "Processing bybit_kline_fixture_v1_55.json: LOAD -> NORMALIZE -> VALIDATE_TIMESTAMPS -> GENERATE_MANIFEST_PREVIEW"
  ],
  "records_processed_count": 4,
  "validation_errors": []
}
```
