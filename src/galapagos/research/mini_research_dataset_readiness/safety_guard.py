from __future__ import annotations

from typing import Any


class MiniResearchDatasetReadinessSafetyGuard:
    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        expected_true = [
            "post_consolidation_review_executed",
            "dataset_seed_design_executed",
            "anti_leakage_plan_created",
            "approval_gate_only",
            "reports_only",
            "no_new_data_directory_writes",
            "no_strategy_validated",
            "no_paper_live",
            "no_real_trading",
            "dataset_seed_design_created",
            "dataset_seed_plan_reports_only",
            "dataset_seed_plan_theoretical_paths_only",
            "future_dataset_seed_requires_v1_91_approval",
            "future_dataset_seed_no_network",
            "future_dataset_seed_no_ml",
            "future_dataset_seed_no_trading",
            "future_dataset_seed_no_full_dataset",
            "causal_timestamp_policy_defined",
            "available_ts_policy_defined",
            "event_ts_policy_defined",
            "decision_ts_policy_defined",
            "feature_available_ts_lte_decision_ts_rule_defined",
            "no_lookahead_policy_defined",
            "provenance_policy_defined",
            "manifest_checksum_policy_defined",
            "schema_validation_policy_defined",
        ]
        expected_false = [
            "dataset_seed_created",
            "dataset_created",
            "data_contract_actual_write_executed",
            "materialization_executed",
            "new_materialization_executed",
            "scope_drift_detected",
            "data_directory_writes_allowed",
            "data_directory_write_attempted",
            "new_data_files_created",
            "existing_data_files_modified",
            "existing_v1_84_files_modified",
            "existing_v1_87_files_modified",
            "existing_v1_90_files_modified",
            "research_dataset_updated",
            "network_executed",
            "new_network_requests_executed",
            "pagination_used",
            "authenticated_request_allowed",
            "secrets_used",
            "strategy_link_allowed",
            "trading_allowed",
            "real_orders_possible",
            "holdout_executed",
            "codex_cli_called",
            "ml_signal_validation_executed",
            "predictions_created",
            "labels_created",
            "targets_created",
            "v1_92_execution_attempted",
            "forbidden_file_types_detected",
            "parquet_created",
            "csv_created",
            "sqlite_created",
            "jsonl_created",
            "db_created",
        ]
        for field in expected_true:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")
        for field in expected_false:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")
        if payload.get("request_retry_count") != 0:
            issues.append("request_retry_count != 0")
        if payload.get("physical_files_created_count") != 0:
            issues.append("physical_files_created_count != 0")
        if payload.get("future_dataset_seed_allowed_root") != "data/research/dataset_seed/v1_92/":
            issues.append("future_dataset_seed_allowed_root mismatch")
        if payload.get("future_dataset_seed_max_files", 99) > 5:
            issues.append("future_dataset_seed_max_files > 5")
        if payload.get("future_dataset_seed_max_bytes", 999_999) > 50_000:
            issues.append("future_dataset_seed_max_bytes > 50000")
        if payload.get("future_dataset_seed_allowed_extensions") != [".json"]:
            issues.append("future_dataset_seed_allowed_extensions mismatch")
        if payload.get("future_dataset_rows_preview_limit", 99) > 10:
            issues.append("future_dataset_rows_preview_limit > 10")
        return {"safety_check_passed": not issues, "safety_issues": issues}
