# Manifest Dryrun Validation

Validates manifest structure and metadata.

- **Version**: V1.60.2
- **Status**: PASSED

```json
{
  "status": "PASSED",
  "manifest_dryrun_validation_status": "COMPLETED",
  "manifest_preview_generated": true,
  "manifest_data_file_created": false,
  "previews": [
    {
      "source": "MOCK_EXCHANGE",
      "symbol": "BTC/USDT",
      "timeframe": "1m",
      "request_window": "2026-05-13 11:00:00 to 2026-05-13 12:00:00",
      "expected_rows": 2,
      "actual_rows_preview": 2,
      "available_ts_policy": "CAUSAL_SEQUENCE",
      "ingest_ts_policy": "CAUSAL_SEQUENCE",
      "checksum_policy": "SHA256_EXPECTED",
      "no_lookahead_confirmation": true
    },
    {
      "source": "MOCK_EXCHANGE",
      "symbol": "BTC/USDT",
      "timeframe": "1m",
      "request_window": "2026-05-13 11:00:00 to 2026-05-13 12:00:00",
      "expected_rows": 2,
      "actual_rows_preview": 2,
      "available_ts_policy": "CAUSAL_SEQUENCE",
      "ingest_ts_policy": "CAUSAL_SEQUENCE",
      "checksum_policy": "SHA256_EXPECTED",
      "no_lookahead_confirmation": true
    }
  ],
  "schema_validation": "SUCCESSFUL"
}
```
