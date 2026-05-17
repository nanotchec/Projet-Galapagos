# Microstructure Causal Timestamp Policy

```json
{
  "status": "CAUSAL_TIMESTAMP_POLICY_DEFINED",
  "policy": {
    "event_ts": "Timestamp of the actual market event",
    "available_ts": "event_ts + network_latency_buffer (e.g. 50ms)",
    "decision_ts": "Timestamp when the strategy evaluates the feature",
    "ingest_ts": "Timestamp when the data was saved to disk (irrelevant for backtest, but tracked for provenance)",
    "anti_leakage_rule": "available_ts MUST be strictly < decision_ts for any feature to be used."
  },
  "alignment_with_v1_52": true,
  "migrated_from": "V1.53",
  "migration_reason": "release JSON hygiene fix"
}
```
