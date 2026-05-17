# Microstructure Adapter Refinement Audit V1 55 2

```json
{
  "version": "V1.55.2",
  "previous_base": "V1.55.1",
  "binance": {
    "source": "binance",
    "status": "REFINED_STUB",
    "mapped_fields": [
      "open",
      "high",
      "low",
      "close",
      "volume",
      "quote_volume",
      "trade_count",
      "taker_buy_base_volume",
      "taker_buy_quote_volume"
    ],
    "missing_fields": [],
    "timestamp_precision": "ms",
    "causality_policy": "STRICT_CLOSE_TIME"
  },
  "bybit": {
    "source": "bybit",
    "status": "PARTIAL_REFINED_STUB",
    "mapped_fields": [
      "open",
      "high",
      "low",
      "close",
      "volume",
      "quote_volume"
    ],
    "missing_fields": [
      "trade_count",
      "taker_buy_base_volume",
      "taker_buy_quote_volume"
    ],
    "timestamp_precision": "ms",
    "causality_policy": "ESTIMATED_FROM_TIMEFRAME"
  },
  "adapter_refinement_audit_status": "PASSED"
}
```
