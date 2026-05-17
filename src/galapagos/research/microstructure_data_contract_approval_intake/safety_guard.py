from typing import Any, Dict, List

STRICT_REQUIRED_INVARIANTS = [
    # Network (6)
    {"field": "network_executed", "expected_value": False, "category": "Network", "failure_code": "UNAUTHORIZED_NETWORK"},
    {"field": "new_network_requests_executed", "expected_value": False, "category": "Network", "failure_code": "UNAUTHORIZED_NETWORK_REQUESTS"},
    {"field": "request_retry_count", "expected_value": 0, "category": "Network", "failure_code": "UNAUTHORIZED_RETRY"},
    {"field": "pagination_used", "expected_value": False, "category": "Network", "failure_code": "UNAUTHORIZED_PAGINATION"},
    {"field": "authenticated_request_allowed", "expected_value": False, "category": "Network", "failure_code": "UNAUTHORIZED_AUTH_REQUEST"},
    {"field": "secrets_used", "expected_value": False, "category": "Network", "failure_code": "UNAUTHORIZED_SECRETS_USAGE"},
    
    # Data Write (12)
    {"field": "data_directory_writes_allowed", "expected_value": False, "category": "Data", "failure_code": "UNAUTHORIZED_DATA_WRITE_PERM"},
    {"field": "new_data_files_created", "expected_value": False, "category": "Data", "failure_code": "UNAUTHORIZED_DATA_FILE_CREATION"},
    {"field": "no_data_directory_writes", "expected_value": True, "category": "Data", "failure_code": "DATA_WRITE_DETECTED"},
    {"field": "parquet_created", "expected_value": False, "category": "Data", "failure_code": "PARQUET_FILE_DETECTED"},
    {"field": "csv_created", "expected_value": False, "category": "Data", "failure_code": "CSV_FILE_DETECTED"},
    {"field": "sqlite_created", "expected_value": False, "category": "Data", "failure_code": "SQLITE_FILE_DETECTED"},
    {"field": "jsonl_created", "expected_value": False, "category": "Data", "failure_code": "JSONL_FILE_DETECTED"},
    {"field": "db_created", "expected_value": False, "category": "Data", "failure_code": "DB_FILE_DETECTED"},
    {"field": "dataset_created", "expected_value": False, "category": "Data", "failure_code": "DATASET_CREATION_DETECTED"},
    {"field": "research_dataset_updated", "expected_value": False, "category": "Data", "failure_code": "RESEARCH_DATASET_UPDATE_DETECTED"},
    {"field": "data_write_approved", "expected_value": False, "category": "Data", "failure_code": "UNAUTHORIZED_DATA_WRITE_APPROVAL"},
    {"field": "dataset_materialization_approved", "expected_value": False, "category": "Data", "failure_code": "UNAUTHORIZED_DATASET_APPROVAL"},
    
    # Trading / ML (12)
    {"field": "strategy_link_allowed", "expected_value": False, "category": "Trading_ML", "failure_code": "UNAUTHORIZED_STRATEGY_LINK"},
    {"field": "trading_allowed", "expected_value": False, "category": "Trading_ML", "failure_code": "UNAUTHORIZED_TRADING_PERM"},
    {"field": "no_strategy_validated", "expected_value": True, "category": "Trading_ML", "failure_code": "STRATEGY_VALIDATION_DETECTED"},
    {"field": "no_paper_live", "expected_value": True, "category": "Trading_ML", "failure_code": "PAPER_LIVE_DETECTED"},
    {"field": "no_real_trading", "expected_value": True, "category": "Trading_ML", "failure_code": "REAL_TRADING_DETECTED"},
    {"field": "real_orders_possible", "expected_value": False, "category": "Trading_ML", "failure_code": "REAL_ORDER_CAPABILITY_DETECTED"},
    {"field": "holdout_executed", "expected_value": False, "category": "Trading_ML", "failure_code": "HOLDOUT_EXECUTION_DETECTED"},
    {"field": "codex_cli_called", "expected_value": False, "category": "Trading_ML", "failure_code": "CODEX_CLI_USAGE_DETECTED"},
    {"field": "ml_signal_validation_executed", "expected_value": False, "category": "Trading_ML", "failure_code": "ML_SIGNAL_VALIDATION_DETECTED"},
    {"field": "predictions_created", "expected_value": False, "category": "Trading_ML", "failure_code": "PREDICTIONS_DETECTED"},
    {"field": "labels_created", "expected_value": False, "category": "Trading_ML", "failure_code": "LABELS_DETECTED"},
    {"field": "targets_created", "expected_value": False, "category": "Trading_ML", "failure_code": "TARGETS_DETECTED"},
    
    # Scope Drift (3)
    {"field": "v1_82_execution_attempted", "expected_value": False, "category": "Scope", "failure_code": "V1_82_EXECUTION_DRIFT"},
    {"field": "data_contract_dryrun_executed", "expected_value": False, "category": "Scope", "failure_code": "DATA_CONTRACT_DRYRUN_DRIFT"},
    {"field": "scope_drift_detected", "expected_value": False, "category": "Scope", "failure_code": "GENERIC_SCOPE_DRIFT"}
]

class SafetyGuard:
    def check_safety(self, state: Dict[str, Any]) -> Dict[str, Any]:
        failed_invariants = []
        passed_invariants = []
        category_counts = {}
        
        for inv in STRICT_REQUIRED_INVARIANTS:
            field = inv["field"]
            expected = inv["expected_value"]
            category = inv["category"]
            
            category_counts[category] = category_counts.get(category, 0) + 1
            
            actual = state.get(field)
            if actual != expected:
                failed_invariants.append({
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                    "failure_code": inv["failure_code"]
                })
            else:
                passed_invariants.append(field)
                
        return {
            "safety_check_passed": len(failed_invariants) == 0,
            "checked_invariants_count": len(STRICT_REQUIRED_INVARIANTS),
            "failed_invariants_count": len(failed_invariants),
            "failed_invariants": failed_invariants,
            "passed_invariants": passed_invariants,
            "category_counts": category_counts,
            "infrastructure_only_preserved": len(failed_invariants) == 0
        }
