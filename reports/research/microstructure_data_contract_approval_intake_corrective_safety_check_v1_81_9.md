# Microstructure Data Contract Approval Intake Corrective Safety Check V1 81 9

```json
{
  "safety_check_passed": false,
  "checked_invariants_count": 33,
  "failed_invariants_count": 28,
  "failed_invariants": [
    {
      "field": "new_network_requests_executed",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_NETWORK_REQUESTS"
    },
    {
      "field": "request_retry_count",
      "expected": 0,
      "actual": null,
      "failure_code": "UNAUTHORIZED_RETRY"
    },
    {
      "field": "pagination_used",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_PAGINATION"
    },
    {
      "field": "authenticated_request_allowed",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_AUTH_REQUEST"
    },
    {
      "field": "secrets_used",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_SECRETS_USAGE"
    },
    {
      "field": "new_data_files_created",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_DATA_FILE_CREATION"
    },
    {
      "field": "no_data_directory_writes",
      "expected": true,
      "actual": null,
      "failure_code": "DATA_WRITE_DETECTED"
    },
    {
      "field": "parquet_created",
      "expected": false,
      "actual": null,
      "failure_code": "PARQUET_FILE_DETECTED"
    },
    {
      "field": "csv_created",
      "expected": false,
      "actual": null,
      "failure_code": "CSV_FILE_DETECTED"
    },
    {
      "field": "sqlite_created",
      "expected": false,
      "actual": null,
      "failure_code": "SQLITE_FILE_DETECTED"
    },
    {
      "field": "jsonl_created",
      "expected": false,
      "actual": null,
      "failure_code": "JSONL_FILE_DETECTED"
    },
    {
      "field": "db_created",
      "expected": false,
      "actual": null,
      "failure_code": "DB_FILE_DETECTED"
    },
    {
      "field": "dataset_created",
      "expected": false,
      "actual": null,
      "failure_code": "DATASET_CREATION_DETECTED"
    },
    {
      "field": "research_dataset_updated",
      "expected": false,
      "actual": null,
      "failure_code": "RESEARCH_DATASET_UPDATE_DETECTED"
    },
    {
      "field": "data_write_approved",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_DATA_WRITE_APPROVAL"
    },
    {
      "field": "dataset_materialization_approved",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_DATASET_APPROVAL"
    },
    {
      "field": "strategy_link_allowed",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_STRATEGY_LINK"
    },
    {
      "field": "trading_allowed",
      "expected": false,
      "actual": null,
      "failure_code": "UNAUTHORIZED_TRADING_PERM"
    },
    {
      "field": "no_strategy_validated",
      "expected": true,
      "actual": null,
      "failure_code": "STRATEGY_VALIDATION_DETECTED"
    },
    {
      "field": "no_paper_live",
      "expected": true,
      "actual": null,
      "failure_code": "PAPER_LIVE_DETECTED"
    },
    {
      "field": "no_real_trading",
      "expected": true,
      "actual": null,
      "failure_code": "REAL_TRADING_DETECTED"
    },
    {
      "field": "holdout_executed",
      "expected": false,
      "actual": null,
      "failure_code": "HOLDOUT_EXECUTION_DETECTED"
    },
    {
      "field": "codex_cli_called",
      "expected": false,
      "actual": null,
      "failure_code": "CODEX_CLI_USAGE_DETECTED"
    },
    {
      "field": "ml_signal_validation_executed",
      "expected": false,
      "actual": null,
      "failure_code": "ML_SIGNAL_VALIDATION_DETECTED"
    },
    {
      "field": "predictions_created",
      "expected": false,
      "actual": null,
      "failure_code": "PREDICTIONS_DETECTED"
    },
    {
      "field": "labels_created",
      "expected": false,
      "actual": null,
      "failure_code": "LABELS_DETECTED"
    },
    {
      "field": "targets_created",
      "expected": false,
      "actual": null,
      "failure_code": "TARGETS_DETECTED"
    },
    {
      "field": "scope_drift_detected",
      "expected": false,
      "actual": null,
      "failure_code": "GENERIC_SCOPE_DRIFT"
    }
  ],
  "passed_invariants": [
    "network_executed",
    "data_directory_writes_allowed",
    "real_orders_possible",
    "v1_82_execution_attempted",
    "data_contract_dryrun_executed"
  ],
  "category_counts": {
    "Network": 6,
    "Data": 12,
    "Trading_ML": 12,
    "Scope": 3
  },
  "infrastructure_only_preserved": false
}
```
