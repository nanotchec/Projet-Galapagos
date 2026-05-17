# Microstructure Data Contract Plan

```json
{
  "data_contract_plan_created": true,
  "data_contract_dryrun_only": true,
  "future_data_write_requires_human_approval": true,
  "plan_details": {
    "source": "Binance public unauthenticated trades endpoint preview from V1.79",
    "symbol": "BTCUSDT",
    "expected_raw_fields": [
      "id",
      "price",
      "qty",
      "quoteQty",
      "time",
      "isBuyerMaker",
      "isBestMatch"
    ],
    "normalized_schema_candidate": [
      "provider",
      "symbol",
      "trade_id",
      "price_decimal_string",
      "quantity_decimal_string",
      "quote_quantity_decimal_string",
      "exchange_timestamp_ms",
      "is_buyer_maker",
      "is_best_match",
      "request_index",
      "source_status_code",
      "collected_at_utc"
    ],
    "quality_checks_candidate": [
      "status_code non-null",
      "status_code == 200",
      "required fields present",
      "numeric strings parseable",
      "timestamp integer milliseconds",
      "no duplicate provider/symbol/trade_id within preview",
      "monotonicity check within request when applicable",
      "no lookahead labels",
      "no strategy fields",
      "no target labels",
      "no predictions",
      "no trading decisions"
    ],
    "future_dry_run_output": {
      "must_remain_inside_reports_research_only": true,
      "must_not_create_data_directory": true,
      "must_not_create_parquet_csv_sqlite_jsonl_db": true,
      "must_not_create_dataset": true
    }
  }
}
```
