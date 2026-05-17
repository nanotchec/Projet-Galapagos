# Microstructure Manifest Schema

```json
{
  "status": "MANIFEST_SCHEMA_DEFINED",
  "schema_fields": {
    "source": "string",
    "symbol": "string",
    "timeframe": "string",
    "start_ts": "integer (ms)",
    "end_ts": "integer (ms)",
    "row_count_expected": "integer",
    "row_count_actual": "integer",
    "file_hash_expected": "string (null in dry-run)",
    "file_hash_actual": "string",
    "ingest_ts": "integer (ms)",
    "available_ts_policy": "string",
    "no_lookahead": "boolean"
  },
  "validation_rules": [
    "start_ts < end_ts",
    "row_count_expected > 0",
    "ingest_ts >= end_ts",
    "no_lookahead must be true"
  ],
  "migrated_from": "V1.53.1",
  "migration_reason": "project state alignment fix"
}
```
