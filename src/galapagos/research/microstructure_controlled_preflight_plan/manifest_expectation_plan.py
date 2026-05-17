def define_manifest_plan(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "manifest_expectations_defined": True,
        "required_manifest_fields": [
            "source", "symbol", "timeframe", "request_window",
            "expected_rows", "actual_rows", "available_ts",
            "ingest_ts", "checksum", "no_lookahead_flag"
        ],
        "validation_strategy": "STRICT_SCHEMA_ENFORCEMENT",
        "timestamp_policy": "CAUSAL_ORDER_ONLY",
        "plan_status": "READY"
    }
